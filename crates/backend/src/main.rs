use axum::{
    routing::{get, post},
    Router,
    extract::State,
    Json,
    response::IntoResponse,
    http::StatusCode,
};
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer};
use sqlx::SqlitePool;
use std::sync::Arc;

pub mod handlers;
pub mod services;
pub mod db;

pub struct AppState {
    pub db: SqlitePool,
}

#[tokio::main]
async fn main() {
    // Initialize Database
    let db_pool = db::sqlite::init_db().await.expect("Failed to initialize database");
    let state = Arc::new(AppState { db: db_pool });

    // Setup CORS
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_headers(Any)
        .allow_methods(Any);

    // Build our application with a route
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/scrape", post(scrape_and_save))
        .route("/history", get(get_history))
        .with_state(state)
        .layer(cors);

    // Run our app
    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    println!("Backend listening on {}", addr);
    
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn health_check() -> &'static str {
    "Backend is healthy!"
}

async fn scrape_and_save(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<shared::dto::ScrapeRequest>,
) -> impl IntoResponse {
    match services::fetch_service::fetch_url(&payload.url).await {
        Ok(html) => {
            let result = services::parse_service::parse_html(&payload.url, &html);
            // Save to DB
            let _ = db::sqlite::save_result(&state.db, &result).await;
            (StatusCode::OK, Json(result)).into_response()
        }
        Err(e) => {
            (StatusCode::BAD_REQUEST, Json(e)).into_response()
        }
    }
}

async fn get_history(
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    match db::sqlite::get_history(&state.db).await {
        Ok(history) => (StatusCode::OK, Json(history)).into_response(),
        Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, Json(e)).into_response(),
    }
}
