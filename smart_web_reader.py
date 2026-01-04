import asyncio
import os
from dotenv import load_dotenv
from langchain.tools import tool
from crawl4ai import AsyncWebCrawler, LLMContentFilter, DefaultMarkdownGenerator
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig, CacheMode

load_dotenv()

@tool("extract_link")
async def extract_link(urls):
    """
    Belirtilen bir veya birden fazla URL'den ana içeriği asenkron olarak çeker.
    
    Crawl4AI ve Gemini LLM kullanarak sayfadaki reklam, menü ve footer gibi 
    gereksiz kalabalığı temizler; geriye sadece temiz bir Markdown içeriği döner.

    Args:
        urls (str | list[str]): İçeriği çekilecek web sayfası URL'si veya URL listesi.

    Returns:
        list[str]: Her bir URL için temizlenmiş Markdown içerik listesi.
    """

    # Tarayıcı yapılandırması
    browser_config = BrowserConfig()

    # İçerik temizleme için LLM yapılandırması (Gemini 2.0 Flash)
    gemini_config = LLMConfig(
        provider="gemini/gemini-2.0-flash",
        api_token=os.getenv("GOOGLE_API_KEY")
    )

    # LLM'e içeriği nasıl filtreleyeceği konusunda verilen talimatlar
    content_filter = LLMContentFilter(
        llm_config=gemini_config,
        instruction="""
        Sen akıllı bir içerik temizleyicisin. SADECE ana makale gövdesini çıkar.
        
        # DAHİL ET:
        - Konuyu açıklayan metinler, teknik ayrıntılar ve adım adım rehberler.
        - Makale başlığı, alt başlıklar (#, ##, ###) ve ilgili kod örnekleri.
        
        # HARİÇ TUT:
        - Navigasyon, menüler, footer, reklamlar ve yan paneller.
        - Yorum formları, 'Benzer yazılar', sosyal medya butonları ve yazar kartları.
        - Görseller, dekoratif ikonlar ve istatistik listeleri.
        
        # ÇIKTI FORMATI:
        - Temiz Markdown kullan. Kod bloklarını dil etiketleriyle (```python vb.) belirt.
        """,
        verbose=True
    )

    # Markdown oluşturucu: Linkleri görmezden gelerek sadece metne odaklanır
    md_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={"ignore_links": True},
    )

    # Tarama ayarları
    run_config = CrawlerRunConfig(
        markdown_generator=md_generator,
        exclude_external_links=True,
        remove_overlay_elements=True,
        process_iframes=False,
        cache_mode=CacheMode.BYPASS,
        stream=False
    )

    markdowns = []
    
    # Asenkron tarayıcıyı başlat
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Tek URL veya liste gelme durumunu yönet
        url_list = [urls] if isinstance(urls, str) else urls
        results = await crawler.arun_many(url_list, config=run_config)

        for res in results:
            if res.success:
                # fit_markdown (temizlenmiş) yoksa raw_markdown kullan
                content = (res.markdown.fit_markdown or res.markdown.raw_markdown or "").strip()
                markdowns.append(content)
            else:
                markdowns.append(f"Hata ({res.url}): {res.error_message}")

    return markdowns
