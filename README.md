# Agent_TOOLS
Bu depo, LangChain tabanlı AI ajanlarının yeteneklerini artırmak için geliştirilmiş özel araçlar (custom tools) koleksiyonudur. Ajanların dış dünya ile etkileşime girmesini, karmaşık veri işlemlerini yapmasını ve API entegrasyonlarını kolaylaştırmayı amaçlar.

🚀 LangChain Persistent Agent Tools
Bu depo, LangChain tabanlı yapay zeka ajanlarının işletim sistemiyle durumsal (stateful) etkileşim kurmasını sağlayan gelişmiş bir araç setidir. Standart shell araçlarının aksine, bu implementasyon terminal oturumunu arka planda canlı tutarak ajanların karmaşık ve çok adımlı görevleri (dizin değiştirme, ortam değişkeni atama, uzun süreli süreç yönetimi) sanki bir insan geliştiriciymiş gibi yapmasına olanak tanır.

🔥 Neden Bu Araca İhtiyacınız Var?
Klasik LLM shell araçları her komut için yeni bir süreç (process) başlatır. Bu durum şu sorunlara yol açar:

cd /yol/ komutu çalışır ama bir sonraki komut yine ana dizinde başlar.

Tanımlanan export veya set değişkenleri kaybolur.

Python sanal ortamları (venv) aktive edilemez.

Bu araç, tüm bu kısıtlamaları ortadan kaldırır.

✨ Temel Özellikler
Persistent Session Architecture: Komutlar arasında cwd (çalışma dizini), çevre değişkenleri ve oturum geçmişi korunur.

Cross-Platform Compatibility: * Windows: PowerShell Core veya CMD desteği.

Unix/Linux/macOS: Bash, Zsh veya Sh desteği.

Base64 Command Wrapping: Komutlar iletilmeden önce Base64 ile sarmalanır. Bu sayede tırnak işaretleri (", ') veya özel karakterlerden kaynaklanan syntax hataları tamamen engellenir.

Sentinel-Based Output Tracking: Her komutun çıktısı benzersiz bir UUID (Sentinel) ile izlenir. Bu, asenkron okuma sırasında çıktının nerede bittiğini ve exit code'un ne olduğunu kesin olarak belirler.

Thread-Safe Async Lock: asyncio.Lock mekanizması sayesinde, ajanın aynı anda birden fazla komut göndererek terminali bozması engellenir.

🛠️ Araç Seti Referansı
1. shell_exec
Ajanın işletim sistemi üzerinde komut koşturmasını sağlar.

Girdi: command (str) - Çalıştırılacak tam shell komutu.

Çıktı: * stdout: Komutun terminal çıktısı.

exit_code: İşlem başarı durumu (0 = Başarılı).

session_id: Oturumun benzersiz kimliği.

2. close_shell
Aktif terminal oturumunu ve bağlı alt süreçleri (subprocesses) güvenli bir şekilde sonlandırır. Bellek sızıntılarını önlemek için görev sonunda çağrılması önerilir.

🚀 Hızlı Başlangıç
Kurulum
Bash

pip install langchain langchain-openai
Örnek Kullanım (LangChain)
Python

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from your_module import shell_exec, close_shell

llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [shell_exec, close_shell]

agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Ajan artık şu tip karmaşık görevleri yapabilir:
# "Bir proje klasörü oluştur, içine gir, bir venv yarat ve 'requests' kütüphanesini yükle."
🛡️ Güvenlik Uyarısı
Bu araç, LLM'e sisteminizde komut çalıştırma yetkisi verir. Üretim ortamlarında (production) kullanırken Docker konteynerları veya izole edilmiş (sandboxed) ortamlar kullanmanız şiddetle tavsiye edilir.
