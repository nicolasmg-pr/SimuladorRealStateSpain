# UI framework references (fetched official docs)

Working-agreement log: official docs consulted before framework-specific UI work.

## Floating chat (2026-08-10, Streamlit v1.61 docs)

- `st.popover` — https://docs.streamlit.io/develop/api-reference/layout/st.popover
  Standard widgets allowed inside; interacting with widgets inside an open popover
  reruns the app **keeping the popover open**; don't nest popovers.
- `st.chat_input` — https://docs.streamlit.io/develop/api-reference/chat/st.chat_input
  Pinned to page bottom only at top level; inside containers (popover, columns, tabs)
  it renders inline — supported pattern for embedded chatbots.
- OpenRouter chat completions — https://openrouter.ai/docs/api-reference/chat-completion
  OpenAI-compatible `POST /api/v1/chat/completions`, Bearer auth. Reasoning models may
  return the chain of thought in `message.reasoning` and/or `<think>` blocks in
  `message.content`; the UI strips those (`src/resim/ui/chat.py`).
