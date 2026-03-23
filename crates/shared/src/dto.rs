use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ScrapeRequest {
    pub url: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ScrapeResult {
    pub url: String,
    pub title: String,
    pub headings: Vec<String>,
    pub paragraphs: Vec<String>,
    pub links: Vec<String>,
    pub timestamp: String,
}
