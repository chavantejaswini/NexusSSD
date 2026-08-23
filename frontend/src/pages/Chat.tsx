import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendChat } from "../api/chat";
import type { AgentStep } from "../api/types";
import { Card } from "../components/ui";

interface Message {
  role: "user" | "assistant";
  content: string;
  agents?: string[];
  trace?: AgentStep[];
}

const SUGGESTIONS = [
  "Which drives are most likely to fail this month and why?",
  "How many drives are in the fleet and how many failed?",
  "When should I replace a high-risk drive?",
  "Which drives are running hottest right now?",
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const scrollRef = useRef<HTMLDivElement>(null);

  const chat = useMutation({
    mutationFn: (msg: string) => sendChat(msg, sessionId),
    onSuccess: (res) => {
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, agents: res.agents, trace: res.trace },
      ]);
      queueMicrotask(() => scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight));
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "The assistant is unavailable. Is the API running?" },
      ]);
    },
  });

  const submit = (text: string) => {
    const msg = text.trim();
    if (!msg || chat.isPending) return;
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setInput("");
    chat.mutate(msg);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <h1 className="mb-4 text-2xl font-semibold">AI Chat Assistant</h1>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-auto pr-1">
        {messages.length === 0 && (
          <Card title="Ask about the fleet">
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/5"
                >
                  {s}
                </button>
              ))}
            </div>
          </Card>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
                m.role === "user"
                  ? "bg-nexus-accent/20 text-slate-100"
                  : "border border-white/10 bg-nexus-panel/60 text-slate-200"
              }`}
            >
              <div className="whitespace-pre-wrap">{m.content}</div>
              {m.agents && m.agents.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1 border-t border-white/10 pt-2">
                  {m.agents.map((a, j) => (
                    <span
                      key={`${a}-${j}`}
                      className="rounded-full bg-black/30 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {chat.isPending && (
          <div className="text-sm text-slate-500">The agents are working…</div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
        className="mt-4 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about drive health, risk, or maintenance…"
          className="flex-1 rounded-md border border-white/10 bg-black/20 px-3 py-2 text-sm outline-none focus:border-nexus-accent"
        />
        <button
          type="submit"
          disabled={chat.isPending}
          className="rounded-md bg-nexus-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
