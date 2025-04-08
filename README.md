# MCPML Browser Recorder

## Usage

```bash
uvx --from git+https://github.com/a5c-ai/mcpml#egg=mcpml mcpml run -c https://github.com/a5c-ai/mcpml-browser-recorder.git --transport=sse
```

or

```bash
git clone https://github.com/a5c-ai/mcpml-browser-recorder.git
cd mcpml-browser-recorder
sh ./install-deps.sh
uvx --from git+https://github.com/a5c-ai/mcpml#egg=mcpml mcpml run --transport=sse
```

## Tools

### record_session_agent

Records a browsing session.
