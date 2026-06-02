import json
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from medevidence_agent.config import settings
from medevidence_agent.workflow import run_workflow


HISTORY_PATH = Path(__file__).resolve().parents[2] / "data" / "history.json"


class MedEvidenceApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("MedEvidence Agent")
        self.root.geometry("1120x780")
        self.root.minsize(920, 640)

        self.question_var = tk.StringVar()
        self.status_var = tk.StringVar(value="就绪")
        self.current_references: list[str] = []
        self.history_items = self._load_history()

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=16)
        top.pack(fill="x")

        ttk.Label(top, text="请输入医学问题", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")

        question_entry = ttk.Entry(top, textvariable=self.question_var, font=("Microsoft YaHei UI", 11))
        question_entry.pack(fill="x", pady=(8, 8))
        question_entry.insert(0, "糖尿病伴蛋白尿时高血压首选什么药？")

        action_row = ttk.Frame(top)
        action_row.pack(fill="x")

        self.run_button = ttk.Button(action_row, text="开始分析", command=self.run_analysis)
        self.run_button.pack(side="left")

        ttk.Button(action_row, text="复制结论", command=self.copy_summary).pack(side="left", padx=(8, 0))
        ttk.Button(action_row, text="导出结果", command=self.export_summary).pack(side="left", padx=(8, 0))
        ttk.Button(action_row, text="打开首个来源", command=self.open_first_reference).pack(side="left", padx=(8, 0))

        ttk.Label(action_row, textvariable=self.status_var).pack(side="right")

        history_row = ttk.Frame(top)
        history_row.pack(fill="x", pady=(10, 0))
        ttk.Label(history_row, text="历史问题").pack(side="left")
        self.history_box = ttk.Combobox(history_row, values=self.history_items, state="readonly")
        self.history_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.history_box.bind("<<ComboboxSelected>>", self._apply_history_item)

        progress_row = ttk.Frame(top)
        progress_row.pack(fill="x", pady=(10, 0))
        self.progress = ttk.Progressbar(progress_row, orient="horizontal", mode="determinate", maximum=5)
        self.progress.pack(fill="x")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.summary_text = self._add_text_tab(notebook, "最终结论")
        self.plan_text = self._add_text_tab(notebook, "检索计划")
        self.sources_text = self._add_text_tab(notebook, "候选来源")
        self.evidence_text = self._add_text_tab(notebook, "证据抽取")
        self.review_text = self._add_text_tab(notebook, "审核结果")

    def _add_text_tab(self, notebook: ttk.Notebook, title: str) -> ScrolledText:
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=title)

        text = ScrolledText(frame, wrap="word", font=("Microsoft YaHei UI", 10))
        text.pack(fill="both", expand=True)
        text.configure(state="disabled")
        return text

    def _set_text(self, widget: ScrolledText, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state="disabled")

    def _load_history(self) -> list[str]:
        if not HISTORY_PATH.exists():
            return []
        try:
            return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_history(self, question: str) -> None:
        if question in self.history_items:
            self.history_items.remove(question)
        self.history_items.insert(0, question)
        self.history_items = self.history_items[:10]
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(json.dumps(self.history_items, ensure_ascii=False, indent=2), encoding="utf-8")
        self.history_box.configure(values=self.history_items)

    def _apply_history_item(self, _event=None) -> None:
        selected = self.history_box.get().strip()
        if selected:
            self.question_var.set(selected)

    def run_analysis(self) -> None:
        question = self.question_var.get().strip()
        if not question:
            messagebox.showwarning("提示", "请输入一个医学问题。")
            return

        self.run_button.configure(state="disabled")
        self.status_var.set("分析中：准备开始")
        self.progress.configure(value=0, maximum=5)
        self.current_references = []

        for widget in (
            self.summary_text,
            self.plan_text,
            self.sources_text,
            self.evidence_text,
            self.review_text,
        ):
            self._set_text(widget, "")

        self._save_history(question)
        thread = threading.Thread(target=self._run_workflow_thread, args=(question,), daemon=True)
        thread.start()

    def _run_workflow_thread(self, question: str) -> None:
        try:
            state = run_workflow(
                question,
                settings,
                verbose=False,
                progress_callback=self._threadsafe_progress_update,
            )
            self.root.after(0, self._render_state, state)
        except Exception as exc:
            self.root.after(0, self._show_error, exc)

    def _threadsafe_progress_update(self, stage: str, current: int, total: int) -> None:
        self.root.after(0, self._update_progress_ui, stage, current, total)

    def _update_progress_ui(self, stage: str, current: int, total: int) -> None:
        self.progress.configure(maximum=total)
        self.progress["value"] = current
        if current >= total:
            self.status_var.set(f"分析中：{stage}（即将完成）")
        else:
            self.status_var.set(f"分析中：{stage}")

    def _render_state(self, state) -> None:
        if state.plan:
            plan_content = (
                f"Intent:\n{state.plan.intent}\n\n"
                f"Risk Level:\n{state.plan.risk_level}\n\n"
                f"Keywords:\n- " + "\n- ".join(state.plan.keywords)
            )
        else:
            plan_content = "无检索计划。"

        if state.candidate_sources:
            sources_content = "\n---\n".join(
                [
                    f"标题：{item.title}\n年份：{item.year}\n类型：{item.source_type}\n"
                    f"分数：{item.relevance_score:.3f}\n链接：{item.url}"
                    for item in state.candidate_sources
                ]
            )
        else:
            sources_content = "无候选来源。"

        if state.evidence_items:
            evidence_content = "\n---\n".join(
                [
                    f"标题：{item.title}\n结论：{item.claim}\n支持文本：{item.support_text}\n"
                    f"分数：{item.score:.3f}\n类型：{item.source_type}"
                    for item in state.evidence_items
                ]
            )
        else:
            evidence_content = "无抽取证据。"

        if state.verification:
            conflicts = "\n- ".join(state.verification.conflicts) if state.verification.conflicts else "无"
            review_content = (
                f"总结：\n{state.verification.summary_claim}\n\n"
                f"置信度：{state.verification.confidence:.3f}\n"
                f"需要人工审核：{state.verification.needs_human_review}\n\n"
                f"冲突信息：\n- {conflicts}"
            )
        else:
            review_content = "无审核结果。"

        if state.final_answer:
            self.current_references = state.final_answer.references
            references = "\n".join(state.final_answer.references)
            summary_content = f"{state.final_answer.answer}\n\n参考来源：\n{references}"
        else:
            summary_content = "无最终结论。"

        self._set_text(self.plan_text, plan_content)
        self._set_text(self.sources_text, sources_content)
        self._set_text(self.evidence_text, evidence_content)
        self._set_text(self.review_text, review_content)
        self._set_text(self.summary_text, summary_content)

        self.run_button.configure(state="normal")
        self.status_var.set("完成")
        self.progress["value"] = self.progress["maximum"]

    def copy_summary(self) -> None:
        content = self.summary_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("提示", "当前没有可复制的结论。")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("提示", "已复制最终结论。")

    def export_summary(self) -> None:
        content = self.summary_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("提示", "当前没有可导出的结果。")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")],
            title="导出分析结果",
        )
        if not file_path:
            return

        Path(file_path).write_text(content, encoding="utf-8")
        messagebox.showinfo("提示", f"结果已导出到：\n{file_path}")

    def open_first_reference(self) -> None:
        if not self.current_references:
            messagebox.showinfo("提示", "当前没有可打开的参考来源。")
            return

        first_ref = self.current_references[0]
        if " - " in first_ref:
            url = first_ref.split(" - ", 1)[1].strip()
            webbrowser.open(url)
        else:
            messagebox.showwarning("提示", "未能从参考来源中解析出链接。")

    def _show_error(self, exc: Exception) -> None:
        self.run_button.configure(state="normal")
        self.status_var.set("失败")
        messagebox.showerror("运行失败", str(exc))


def launch_gui() -> None:
    root = tk.Tk()
    MedEvidenceApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
