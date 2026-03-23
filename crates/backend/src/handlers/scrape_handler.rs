use axum::{Json, response::IntoResponse, http::StatusCode};
use shared::dto::{ScrapeRequest, ScrapeResult};
use crate::services::{fetch_service, parse_service};

pub async fn scrape(
    Json(payload): Json<ScrapeRequest>,
) -> impl IntoResponse {
    match fetch_service::fetch_url(&payload.url).await {
        Ok(html) => {
            let result = parse_service::parse_html(&payload.url, &html);
            (StatusCode::OK, Json(result)).into_response()
        }
        Err(e) => {
            (StatusCode::BAD_REQUEST, Json(e)).into_response()
        }
    }
}
