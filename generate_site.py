import json
import pathlib

ROOT = pathlib.Path(__file__).parent


# ── Parsers ────────────────────────────────────────────────────────────────────

def parse_responses(path: pathlib.Path) -> list[dict]:
    """Parse llm_council_results.md → [{question, member_name, response}]"""
    results = []
    question = None
    member_name = None
    response_lines = []

    for line in path.read_text().splitlines():
        if line.startswith("## "):
            question = line[3:].strip()
        elif line.startswith("### "):
            if member_name and response_lines:
                results.append({
                    "question": question,
                    "member_name": member_name,
                    "response": "\n".join(response_lines).strip(),
                })
            member_name = line[4:].strip()
            response_lines = []
        elif member_name:
            response_lines.append(line)

    if member_name and response_lines:
        results.append({
            "question": question,
            "member_name": member_name,
            "response": "\n".join(response_lines).strip(),
        })

    return results


# ── HTML template ──────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>LLM Council</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    .prose h1,.prose h2,.prose h3 { font-weight:700; margin:.75rem 0 .5rem; }
    .prose h1{font-size:1.25rem} .prose h2{font-size:1.1rem} .prose h3{font-size:1rem}
    .prose p { margin:.5rem 0; line-height:1.7; }
    .prose ul,.prose ol { margin:.5rem 0 .5rem 1.25rem; }
    .prose li { margin:.25rem 0; }
    .tab-btn.active { background:#6366f1; color:#fff; }
  </style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen font-sans">

  <!-- Header -->
  <header class="bg-indigo-900 border-b border-indigo-700 px-8 py-5 flex items-center gap-3">
    <span class="text-3xl">🏛</span>
    <div>
      <h1 class="text-2xl font-bold tracking-tight">LLM Council</h1>
      <p class="text-indigo-300 text-sm">Multi-persona AI evaluation benchmark</p>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-6 py-10 space-y-14">

    <!-- ── Responses ── -->
    <section>
      <h2 class="text-xl font-semibold text-indigo-300 mb-4 uppercase tracking-widest text-sm">
        Council Responses
      </h2>

      <!-- Question tabs -->
      <div id="q-tabs" class="flex flex-wrap gap-2 mb-6"></div>

      <!-- Response cards -->
      <div id="response-panels"></div>
    </section>

    <!-- ── Judgments ── -->
    <section>
      <h2 class="text-xl font-semibold text-indigo-300 mb-6 uppercase tracking-widest text-sm">
        Judgments
      </h2>
      <div class="grid lg:grid-cols-2 gap-8">

        <!-- Score matrix -->
        <div>
          <h3 class="text-sm font-medium text-gray-400 mb-3">Score Matrix (rows = judge, cols = judged)</h3>
          <div class="overflow-x-auto rounded-xl border border-gray-700">
            <table class="w-full text-sm">
              <thead id="score-thead" class="bg-gray-800 text-gray-300"></thead>
              <tbody id="score-tbody" class="divide-y divide-gray-700"></tbody>
              <tfoot id="score-tfoot" class="bg-gray-800/60 text-gray-300"></tfoot>
            </table>
          </div>
        </div>

        <!-- Bar chart -->
        <div>
          <h3 class="text-sm font-medium text-gray-400 mb-3">Mean Score ± Std Dev per Member</h3>
          <div class="bg-gray-900 rounded-xl border border-gray-700 p-4">
            <canvas id="scoreChart"></canvas>
          </div>
        </div>
      </div>
    </section>

  </main>

  <script>
    window.DATA = __DATA__;

    const { responses, scores, stats, members } = DATA;

    // ── Helpers ──────────────────────────────────────────────────────────────
    function scoreColor(v) {
      const t = v / 100;
      const r = Math.round(220 - t * 160);
      const g = Math.round(60 + t * 150);
      return `rgb(${r},${g},80)`;
    }

    // ── Responses ────────────────────────────────────────────────────────────
    const questions = [...new Set(responses.map(r => r.question))];
    const tabContainer = document.getElementById("q-tabs");
    const panelContainer = document.getElementById("response-panels");

    questions.forEach((q, qi) => {
      // Tab button
      const btn = document.createElement("button");
      btn.className = "tab-btn px-4 py-2 rounded-lg text-sm font-medium bg-gray-800 hover:bg-indigo-700 transition-colors";
      btn.textContent = `Q${qi + 1}: ${q.length > 50 ? q.slice(0, 50) + "…" : q}`;
      btn.title = q;
      btn.onclick = () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".q-panel").forEach(p => p.classList.add("hidden"));
        btn.classList.add("active");
        document.getElementById(`panel-${qi}`).classList.remove("hidden");
      };
      tabContainer.appendChild(btn);

      // Panel
      const panel = document.createElement("div");
      panel.id = `panel-${qi}`;
      panel.className = "q-panel" + (qi > 0 ? " hidden" : "");

      const qAnswers = responses.filter(r => r.question === q);
      panel.innerHTML = `
        <p class="text-gray-400 text-sm mb-4 italic">"${q}"</p>
        <div class="grid md:grid-cols-3 gap-5">
          ${qAnswers.map(r => `
            <div class="bg-gray-900 rounded-xl border border-gray-700 p-5">
              <div class="flex items-center gap-2 mb-3">
                <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
                <span class="font-semibold text-indigo-300 text-sm">${r.member_name}</span>
              </div>
              <div class="prose text-gray-300 text-sm leading-relaxed">
                ${marked.parse(r.response)}
              </div>
            </div>
          `).join("")}
        </div>
      `;
      panelContainer.appendChild(panel);
    });

    // Activate first tab
    tabContainer.firstChild && tabContainer.firstChild.click();

    // ── Score matrix ─────────────────────────────────────────────────────────
    const thead = document.getElementById("score-thead");
    const tbody = document.getElementById("score-tbody");
    const tfoot = document.getElementById("score-tfoot");

    thead.innerHTML = `<tr>
      <th class="px-4 py-3 text-left">Judge →</th>
      ${members.map(m => `<th class="px-4 py-3 text-center">${m}</th>`).join("")}
    </tr>`;

    Object.entries(scores).forEach(([judge, judged]) => {
      tbody.innerHTML += `<tr class="hover:bg-gray-800/40">
        <td class="px-4 py-3 font-medium text-gray-300">${judge}</td>
        ${members.map(m => {
          const v = judged[m] ?? 0;
          return `<td class="px-4 py-3 text-center font-bold" style="color:${scoreColor(v)}">${v}</td>`;
        }).join("")}
      </tr>`;
    });

    tfoot.innerHTML = `
      <tr>
        <td class="px-4 py-3 font-bold text-gray-300">Mean</td>
        ${members.map(m => `<td class="px-4 py-3 text-center font-bold text-yellow-300">${stats[m]?.mean?.toFixed(1) ?? "—"}</td>`).join("")}
      </tr>
      <tr>
        <td class="px-4 py-3 font-bold text-gray-300">Std Dev</td>
        ${members.map(m => `<td class="px-4 py-3 text-center text-gray-400">${stats[m]?.stdev?.toFixed(1) ?? "—"}</td>`).join("")}
      </tr>
    `;

    // ── Bar chart ────────────────────────────────────────────────────────────
    new Chart(document.getElementById("scoreChart"), {
      type: "bar",
      data: {
        labels: members,
        datasets: [{
          label: "Mean Score",
          data: members.map(m => stats[m]?.mean ?? 0),
          backgroundColor: "rgba(99,102,241,0.7)",
          borderColor: "rgba(99,102,241,1)",
          borderWidth: 2,
          borderRadius: 6,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterBody: (items) => {
                const m = members[items[0].dataIndex];
                return `Std Dev: ${stats[m]?.stdev?.toFixed(1) ?? "—"}`;
              }
            }
          }
        },
        scales: {
          y: {
            min: 0, max: 100,
            ticks: { color: "#9ca3af" },
            grid: { color: "#374151" },
          },
          x: { ticks: { color: "#9ca3af" }, grid: { display: false } },
        },
        animation: { duration: 800 },
      },
    });
  </script>
</body>
</html>
"""


def main():
    responses_path = ROOT / "tmp" / "llm_council_results.md"
    judgments_path = ROOT / "tmp" / "llm_council_judgments.json"

    responses = parse_responses(responses_path)
    judgments = json.loads(judgments_path.read_text())

    data = {
        "responses": responses,
        "scores": judgments["scores"],
        "stats": judgments["stats"],
        "members": judgments["members"],
    }

    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))

    out = ROOT / "docs" / "index.html"
    out.write_text(html)
    print(f"Site written to {out}")
    print(f"Open with:  open {out}")


if __name__ == "__main__":
    main()
