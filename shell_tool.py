import asyncio
import os
import platform
import shutil
import uuid
import subprocess
import base64
from functools import partial
from langchain.tools import tool
import inspect

# Aktif shell oturumunu ve session bilgilerini global olarak saklar.
# Bu sayede farklı tool çağrıları aynı terminal oturumuna erişebilir.
SESSION_MAP = {
    "session_id": None,
    "shell": None
}

class PersistentShell:
    """
    İşletim sistemi seviyesinde kalıcı (stateful) bir terminal oturumu yöneten sınıftır.
    Standart shell araçlarının aksine, 'cd' gibi komutların etkisi sonraki komutlarda devam eder.
    """
    def __init__(self, proc=None):
        self.os_name = platform.system().lower()
        self.shell_path = self._detect_shell()
        self.proc = proc  # Aktif subprocess nesnesini tutar.
        self.lock = asyncio.Lock()  # Aynı anda birden fazla komutun karışmasını engeller (Thread-safety).
        self.encoding = "utf-8"  # Çıktıların standart formatı.

    def _detect_shell(self):
        """Sistemde mevcut olan en uygun shell (PowerShell, Bash, Sh vb.) yolunu tespit eder."""
        if self.os_name == "windows":
            return shutil.which("powershell.exe") or shutil.which("cmd.exe")
        for s in ("/bin/bash", "/bin/zsh", "/bin/sh"):
            if path := shutil.which(s):
                return path
        return "/bin/sh"

    async def start(self):
        """Shell sürecini (process) asenkron olarak başlatır ve girdi/çıktı kanallarını açar."""
        if self.proc and self.proc.poll() is None:
            return

        loop = asyncio.get_running_loop()
        shell_command = [self.shell_path]

        # PowerShell için özel parametreler: Profil yüklemez ve etkileşimsiz modda çalışır.
        if "powershell" in self.shell_path.lower():
            shell_command.extend([
                "-NoLogo", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-Command", "-"
            ])

        self.proc = await loop.run_in_executor(
            None,
            partial(
                subprocess.Popen,
                shell_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                encoding=None,
                bufsize=-1,
                creationflags=subprocess.CREATE_NO_WINDOW if self.os_name == "windows" else 0,
            ),
        )

    async def run_command(self, cmd: str, timeout: int = 300):
        """
        Belirtilen komutu açık olan shell oturumunda çalıştırır.
        Base64 kodlama kullanarak özel karakter hatalarını önler ve 'sentinel' ile çıktıyı takip eder.
        """
        async with self.lock:
            if not self.proc or self.proc.poll() is not None:
                await self.start()

            loop = asyncio.get_running_loop()
            # Komutun bittiğini ve çıkış kodunu anlamak için benzersiz bir anahtar üretilir.
            sentinel = f"__END__{uuid.uuid4().hex}__"
            
            if "powershell" in self.shell_path.lower():
                # PowerShell için Base64 sarmalayıcı: Komutu UTF8 olarak çözer ve çalıştırır.
                cmd_bytes = cmd.encode(self.encoding)
                cmd_base64 = base64.b64encode(cmd_bytes).decode('ascii')
                ps_commands = [
                    "function prompt { \" \" }",
                    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8",
                    "$OutputEncoding = [System.Text.Encoding]::UTF8",
                    f"$EncodedCommand = '{cmd_base64}'",
                    "$DecodedCommand = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($EncodedCommand))",
                    "$ScriptBlock = [ScriptBlock]::Create($DecodedCommand)",
                    "$CommandOutput = (Invoke-Command -ScriptBlock $ScriptBlock *>&1 | Out-String)",
                    "if ($?) { $ec = 0 } else { $ec = 1 }",
                    f"Write-Output \"$($CommandOutput){sentinel}$ec\""
                ]
                wrapped_cmd = "; ".join(ps_commands) + "\n"

            elif self.os_name == "windows":  # Standart CMD
                wrapped_cmd = f"chcp 65001 > NUL & prompt $S & {cmd} & echo {sentinel}%ERRORLEVEL%\n"
            else:  # Linux veya macOS (Bash/Sh)
                cmd_bytes = cmd.encode(self.encoding)
                cmd_base64 = base64.b64encode(cmd_bytes).decode('ascii')
                wrapped_cmd = f"echo '{cmd_base64}' | base64 -d | bash; ret=$?; printf '{sentinel}%d\\n' \"$ret\"\n"

            # Komutu shell'in standart girdisine (stdin) gönder.
            await loop.run_in_executor(None, self.proc.stdin.write, wrapped_cmd.encode(self.encoding))
            await loop.run_in_executor(None, self.proc.stdin.flush)

            out_lines = []
            exit_code = None

            try:
                while True:
                    # Satır satır çıktı okunur.
                    line_bytes = await asyncio.wait_for(
                        loop.run_in_executor(None, self.proc.stdout.readline),
                        timeout=timeout
                    )

                    if not line_bytes:
                        exit_code = self.proc.poll() if self.proc.poll() is not None else -1
                        out_lines.append("[HATA: Shell prosesi yanıt vermeden kapandı.]")
                        self.proc = None
                        break

                    line = line_bytes.decode(self.encoding, errors="replace")
                    line_stripped = line.strip()

                    # Çıktı içinde bitiş anahtarı (sentinel) aranır.
                    if sentinel in line_stripped:
                        try:
                            output_part, sentinel_part = line_stripped.split(sentinel, 1)
                            if output_part:
                                out_lines.append(output_part)
                            exit_code = int(sentinel_part) if sentinel_part else -1
                        except (ValueError, IndexError):
                            exit_code = -1
                        break

                    if line_stripped:
                        out_lines.append(line_stripped)

            except asyncio.TimeoutError:
                out_lines.append(f"\n[HATA: Komut {timeout} saniye içinde yanıt vermedi.]")
                await loop.run_in_executor(None, self.proc.terminate)
                self.proc = None
                exit_code = -1

            return {
                "stdout": "\n".join(out_lines).replace("Active code page: 65001", "").strip(),
                "stderr": "",
                "exit_code": exit_code if exit_code is not None else -1,
            }

    async def close(self):
        """Shell sürecini güvenli bir şekilde kapatır ve kaynakları serbest bırakır."""
        if not self.proc or self.proc.poll() is not None:
            return
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self.proc.stdin.write, b"exit\n")
            await loop.run_in_executor(None, self.proc.stdin.flush)
            await loop.run_in_executor(None, partial(self.proc.wait, timeout=2.0))
        except (subprocess.TimeoutExpired, asyncio.TimeoutError):
            await loop.run_in_executor(None, self.proc.terminate)
        finally:
            self.proc = None


@tool("shell_exec", return_direct=False)
async def shell_exec(command: str):
    """
    Kalıcı (stateful) bir terminal oturumunda tek bir shell komutu çalıştırır.
    
    Bu araç, dosya işlemleri, sistem yönetimi ve yazılım geliştirme görevleri için
    ajanın işletim sistemiyle etkileşime girmesini sağlar. Oturum kalıcıdır; 
    bir komutta değiştirilen dizin veya tanımlanan değişken sonraki komutlarda korunur.

    Args:
        command (str): Çalıştırılacak tam shell komutu (Örn: 'ls -la', 'mkdir test').

    Returns:
        dict: Standart çıktı, hata mesajları, çıkış kodu ve oturum ID'sini içeren sözlük.
    """
    if not command:
        return {"stdout": "", "stderr": "Error: Command cannot be empty.", "exit_code": -1}

    # Mevcut bir session yoksa yenisini başlat.
    if SESSION_MAP["shell"] is None or SESSION_MAP["shell"].proc is None:
        session_id = str(uuid.uuid4())
        SESSION_MAP["session_id"] = session_id
        SESSION_MAP["shell"] = PersistentShell()
    else:
        session_id = SESSION_MAP["session_id"]

    shell = SESSION_MAP["shell"]
    result = await shell.run_command(command)

    if shell.proc is None:
        SESSION_MAP["shell"] = None
        SESSION_MAP["session_id"] = None
        result["stderr"] += "\nShell process terminated."

    return {
        "session_id": session_id,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "exit_code": result["exit_code"],
    }


@tool("close_shell", return_direct=False)
async def close_shell():
    """
    Mevcut aktif kalıcı (persistent) shell oturumunu sonlandırır.
    
    Terminal ile ilgili görevler tamamlandığında veya yeni bir temiz oturum 
    gerektiğinde kaynakları serbest bırakmak için bu araç çağrılmalıdır.
    """
    shell = SESSION_MAP.get("shell")
    session_id = SESSION_MAP.get("session_id")

    if shell is None:
        return {"message": "Kapatılacak aktif shell bulunamadı."}

    close_fn = getattr(shell, "close", None)
    if close_fn:
        if inspect.iscoroutinefunction(close_fn):
            await close_fn()
        else:
            close_fn()

    SESSION_MAP["shell"] = None
    SESSION_MAP["session_id"] = None
    return {"message": f"Shell {session_id} başarıyla kapatıldı."}
