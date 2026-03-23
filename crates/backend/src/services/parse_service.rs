use scraper::{Html, Selector};
use shared::dto::ScrapeResult;
use chrono::Utc;

pub fn parse_html(url: &str, html_content: &str) -> ScrapeResult {
    let document = Html::parse_document(html_content);
    
    let title_selector = Selector::parse("title").unwrap();
    let title = document
        .select(&title_selector)
        .next()
        .map(|el| el.text().collect::<Vec<_>>().join(""))
        .unwrap_or_else(|| "No Title".to_string());

    let h_selector = Selector::parse("h1, h2, h3").unwrap();
    let headings = document
        .select(&h_selector)
        .map(|el| el.text().collect::<Vec<_>>().join("").trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    let p_selector = Selector::parse("p").unwrap();
    let paragraphs = document
        .select(&p_selector)
        .map(|el| el.text().collect::<Vec<_>>().join("").trim().to_string())
        .filter(|s| !s.is_empty())
        .take(10) // Limit for now
        .collect();

    let a_selector = Selector::parse("a[href]").unwrap();
    let links = document
        .select(&a_selector)
        .filter_map(|el| el.value().attr("href").map(|s| s.to_string()))
        .filter(|s| s.starts_with("http"))
        .take(20) // Limit for now
        .collect();

    ScrapeResult {
        url: url.to_string(),
        title,
        headings,
        paragraphs,
        links,
        timestamp: Utc::now().to_rfc3339(),
    }
}
