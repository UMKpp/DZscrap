use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use shared::dto::ScrapeResult;
use shared::errors::Error;

pub async fn init_db() -> Result<SqlitePool, Error> {
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect("sqlite:scraper.db?mode=rwc")
        .await
        .map_err(|e| Error::DatabaseError(e.to_string()))?;

    sqlx::query(
        "CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            headings TEXT NOT NULL,
            paragraphs TEXT NOT NULL,
            links TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )"
    )
    .execute(&pool)
    .await
    .map_err(|e| Error::DatabaseError(e.to_string()))?;

    Ok(pool)
}

pub async fn save_result(pool: &SqlitePool, result: &ScrapeResult) -> Result<(), Error> {
    let headings = serde_json::to_string(&result.headings).unwrap();
    let paragraphs = serde_json::to_string(&result.paragraphs).unwrap();
    let links = serde_json::to_string(&result.links).unwrap();

    sqlx::query(
        "INSERT INTO history (url, title, headings, paragraphs, links, timestamp) VALUES (?, ?, ?, ?, ?, ?)"
    )
    .bind(&result.url)
    .bind(&result.title)
    .bind(headings)
    .bind(paragraphs)
    .bind(links)
    .bind(&result.timestamp)
    .execute(pool)
    .await
    .map_err(|e| Error::DatabaseError(e.to_string()))?;

    Ok(())
}

pub async fn get_history(pool: &SqlitePool) -> Result<Vec<ScrapeResult>, Error> {
    let rows = sqlx::query!("SELECT url, title, headings, paragraphs, links, timestamp FROM history ORDER BY id DESC")
        .fetch_all(pool)
        .await
        .map_err(|e| Error::DatabaseError(e.to_string()))?;

    let results = rows.into_iter().map(|row| ScrapeResult {
        url: row.url,
        title: row.title,
        headings: serde_json::from_str(&row.headings).unwrap_or_default(),
        paragraphs: serde_json::from_str(&row.paragraphs).unwrap_or_default(),
        links: serde_json::from_str(&row.links).unwrap_or_default(),
        timestamp: row.timestamp,
    }).collect();

    Ok(results)
}
