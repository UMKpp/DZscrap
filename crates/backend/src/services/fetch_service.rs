use reqwest;
use shared::errors::Error;

pub async fn fetch_url(url: &str) -> Result<String, Error> {
    let client = reqwest::Client::builder()
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        .build()
        .map_err(|e| Error::FetchError(e.to_string()))?;

    let response = client
        .get(url)
        .send()
        .await
        .map_err(|e| Error::FetchError(e.to_string()))?;

    if !response.status().is_success() {
        return Err(Error::FetchError(format!("Request failed with status: {}", response.status())));
    }

    let body = response
        .text()
        .await
        .map_err(|e| Error::FetchError(e.to_string()))?;

    Ok(body)
}
