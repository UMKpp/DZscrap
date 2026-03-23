use leptos::*;
use shared::dto::ScrapeResult;

#[component]
pub fn HistoryList(history: Vec<ScrapeResult>, on_select: Callback<ScrapeResult>) -> impl IntoView {
    view! {
        <div class="history-list">
            <h3>"Recent Scrapes"</h3>
            {history.into_iter().map(|item| {
                let item_clone = item.clone();
                view! {
                    <div class="history-item" on:click=move |_| on_select.call(item_clone.clone())>
                        <span class="history-title">{&item.title}</span>
                        <span class="history-url">{&item.url}</span>
                    </div>
                }
            }).collect::<Vec<_>>()}
        </div>
    }
}
