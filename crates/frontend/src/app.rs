use leptos::*;
use crate::components::url_form::UrlForm;
use crate::components::result_card::ResultCard;
use crate::components::history_list::HistoryList;
use shared::dto::ScrapeResult;
use gloo_net::http::Request;

#[component]
pub fn App() -> impl IntoView {
    let (result, set_result) = create_signal(None::<ScrapeResult>);
    let (loading, set_loading) = create_signal(false);
    let (history, set_history) = create_signal(Vec::<ScrapeResult>::new());

    // Fetch history on mount
    create_effect(move |_| {
        spawn_local(async move {
            let res = Request::get("http://127.0.0.1:3000/history")
                .send()
                .await;
            
            if let Ok(response) = res {
                if let Ok(data) = response.json::<Vec<ScrapeResult>>().await {
                    set_history.set(data);
                }
            }
        });
    });

    let on_select_history = move |res: ScrapeResult| {
        set_result.set(Some(res));
    };

    view! {
        <main class="container">
            <h1>"Rust Web Scraper"</h1>
            <p class="tagline">"Enter a URL to extract titles, headings, and links."</p>
            
            <UrlForm set_result=set_result set_loading=set_loading />

            <div class="content-grid">
                <div class="main-content">
                    {move || {
                        if loading.get() {
                            view! { <div class="loader">"Scraping... please wait"</div> }.into_view()
                        } else if let Some(res) = result.get() {
                            view! { <ResultCard result=res /> }.into_view()
                        } else {
                            view! { <div class="empty-state">"No results yet. Enter a URL above to start."</div> }.into_view()
                        }
                    }}
                </div>

                <div class="sidebar">
                    <HistoryList history=history.get() on_select=Callback::new(on_select_history) />
                </div>
            </div>
        </main>
    }
}
