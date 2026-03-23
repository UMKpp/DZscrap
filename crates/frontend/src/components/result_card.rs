use leptos::*;
use shared::dto::ScrapeResult;

#[component]
pub fn ResultCard(result: ScrapeResult) -> impl IntoView {
    view! {
        <div class="result-card">
            <h2>{result.title}</h2>
            <p class="url">"URL: " {result.url}</p>
            <div class="metadata">
                <span>"Scraped at: " {result.timestamp}</span>
            </div>
            
            <section>
                <h3>"Headings"</h3>
                <ul>
                    {result.headings.into_iter().map(|h| view! { <li>{h}</li> }).collect::<Vec<_>>()}
                </ul>
            </section>

            <section>
                <h3>"Paragraphs"</h3>
                {result.paragraphs.into_iter().map(|p| view! { <p>{p}</p> }).collect::<Vec<_>>()}
            </section>

            <section>
                <h3>"Links"</h3>
                <ul>
                    {result.links.into_iter().map(|l| view! { <li><a href=l.clone() target="_blank">{l}</a></li> }).collect::<Vec<_>>()}
                </ul>
            </section>
        </div>
    }
}
