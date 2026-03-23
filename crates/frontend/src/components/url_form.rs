use leptos::*;
use shared::dto::{ScrapeRequest, ScrapeResult};
use gloo_net::http::Request;

#[component]
pub fn UrlForm(set_result: WriteSignal<Option<ScrapeResult>>, set_loading: WriteSignal<bool>) -> impl IntoView {
    let (url, set_url) = create_signal(String::new());

    let on_submit = move |_| {
        let current_url = url.get();
        if current_url.is_empty() {
            return;
        }

        set_loading.set(true);
        spawn_local(async move {
            let res = Request::post("http://127.0.0.1:3000/scrape")
                .json(&ScrapeRequest { url: current_url })
                .unwrap()
                .send()
                .await;

            match res {
                Ok(response) => {
                    let result: ScrapeResult = response.json().await.unwrap();
                    set_result.set(Some(result));
                }
                Err(_) => {
                    // Handle error
                }
            }
            set_loading.set(false);
        });
    };

    view! {
        <div class="url-form">
            <input
                type="text"
                placeholder="Enter URL to scrape"
                prop:value=url
                on:input=move |ev| set_url.set(event_target_value(&ev))
            />
            <button on:click=on_submit>
                "Scrape"
            </button>
        </div>
    }
}
