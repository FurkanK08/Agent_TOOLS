# Agent_TOOLS
Bu depo, LangChain tabanlı AI ajanlarının yeteneklerini artırmak için geliştirilmiş özel araçlar (custom tools) koleksiyonudur. Ajanların dış dünya ile etkileşime girmesini, karmaşık veri işlemlerini yapmasını ve API entegrasyonlarını kolaylaştırmayı amaçlar.

# 🚀 LangChain Persistent Agent Tools
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

# 🔍 Smart Web Reader: AI-Driven Contextual Content Extraction

**Smart Web Reader**, modern yapay zeka ajanlarının internet üzerindeki yapılandırılmamış ve yüksek gürültülü (reklam, menü, footer vb.) veriyi, yüksek doğrulukla anlamlandırılmış bilgi setlerine dönüştürmesini sağlayan profesyonel bir içerik işleme modülüdür.

Bu araç, **Crawl4AI**'ın tarama gücünü **Gemini 2.0 Flash**'ın anlamsal analiz yeteneğiyle birleştirerek, ajanlar için "saf bağlam" (pure context) üretir.



## 🏗️ Mimari Yaklaşım

Geleneksel scraping yöntemleri (DOM parsing, Regex), modern web sitelerindeki dinamik içerikleri ve gürültüyü temizlemekte yetersiz kalmaktadır. Smart Web Reader, bu süreci üç aşamalı bir "Intelligence Pipeline" üzerinden yönetir:

1.  **Dinamik Render Katmanı:** Headless browser teknolojisi ile JavaScript tabanlı içerikleri ve Single Page Application (SPA) yapılarını tam uyumlulukla simüle eder.
2.  **LLM Tabanlı Semantik Filtreleme:** Gemini 2.0 Flash entegrasyonu sayesinde içerik; reklamlar, navigasyon linkleri ve sosyal medya butonları gibi teknik olmayan öğelerden cerrahi bir hassasiyetle arındırılır.
3.  **Hiyerarşik Markdown Optimizasyonu:** Çıktı, LLM'lerin en yüksek verimle işleyebildiği, başlık hiyerarşisi korunmuş ve kod blokları dil etiketleriyle sanitize edilmiş Markdown formatına dönüştürülür.

## ⚙️ Prompt-Driven Flexibility (Dinamik Prompt Yönetimi)

Smart Web Reader'ın en ayırt edici özelliği, ayıklama mantığının **çalışma anında (runtime)** güncellenebilir olmasıdır. Aracın içerik filtreleme katmanı, doğal dil komutlarını anlar ve extraction stratejisini anlık olarak değiştirir.

### **Dinamik Talimat Güncelleme Yeteneği**
Ajan, ihtiyacına göre `instruction` parametresini güncelleyerek veri çekme odağını anlık olarak yeniden yapılandırabilir:

* **Teknik Odak:** *"Sadece kurulum adımlarını ve API parametrelerini getir."*
* **Finansal Odak:** *"Metindeki tüm döviz kurlarını ve fiyat tablolarını ayıkla."*
* **Akademik Odak:** *"Sadece hipotez, metodoloji ve sonuç kısımlarını özetlemeden getir."*



## ✨ Temel Yetenekler ve Avantajlar

* **Noise Suppression (Gürültü Bastırma):** Navigasyon menüleri, çerez bildirimleri ve yan panel öğeleri gibi ajanın odak noktasını dağıtacak unsurlar %100'e yakın başarıyla elenir.
* **Token Efficiency:** Gereksiz HTML etiketlerini temizleyerek "Context Window" kullanımını optimize eder ve operasyonel maliyetleri (API harcamalarını) düşürür.
* **Technical Content Integrity:** Teknik dökümantasyonlardaki kod bloklarını (Python, Bash, YAML vb.) dil etiketlerini koruyarak doğru formatta sunar.
* **Autonomous Overlay Management:** Pop-up katmanlarını ve rıza metinlerini otomatik olarak kaldırarak doğrudan ana metne odaklanır.

## 📊 Teknik Spesifikasyonlar

| Bileşen | Teknoloji | Fonksiyon |
| :--- | :--- | :--- |
| **Crawling Engine** | Crawl4AI (Async) | Yüksek performanslı asenkron veri toplama. |
| **Reasoning Engine** | Gemini 2.0 Flash | Anlamsal içerik analizi ve filtreleme. |
| **Output Format** | Structured Markdown | Ajan dostu, yüksek kaliteli bilgi çıktısı. |
| **Flexibility** | Prompt-Driven | Dinamik ve güncellenebilir ayıklama talimatları. |

## 🚀 Hızlı Kurulum

 Bağımlılıkları yükleyin
pip install crawl4ai langchain langchain-openai python-dotenv

 Tarayıcı motorlarını hazırlayın
crawl4ai-setup
from your_module import smart_web_reader

# Ajan artık dinamik talimatlarla veri çekebilir

result = await smart_web_reader(
    urls="[https://example.com/article](https://example.com/article)",
    instruction="Sadece teknik karşılaştırma tablolarını ayıkla."
)
crawl4ai-setup
Bu dökümantasyon, aracın sadece bir veri çekme aracı değil, aynı zamanda esnek bir Veri Mühendisliği çözümü olduğunu vurgular.
