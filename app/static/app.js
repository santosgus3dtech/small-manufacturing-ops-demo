const money = (cents) => new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD" }).format(cents / 100);
const role = () => document.querySelector("#role").value;

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { "Content-Type": "application/json", "X-Demo-Role": role(), ...(options.headers || {}) } });
  if (!response.ok) throw new Error((await response.json()).detail || "Request failed");
  return response.json();
}

function metric(label, value, detail) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong><small>${detail}</small></div>`;
}

async function load() {
  const [summary, orders] = await Promise.all([api("/api/dashboard"), api("/api/orders")]);
  document.querySelector("#metrics").innerHTML = [
    metric("Active orders", summary.active_orders, `${summary.total_orders} total in demo`),
    metric("Booked revenue", money(summary.revenue_cents), "Synthetic order book"),
    metric("Gross profit", money(summary.gross_profit_cents), "Revenue minus direct cost"),
    metric("Gross margin", `${summary.gross_margin_percent}%`, "Across seeded orders"),
  ].join("");
  document.querySelector("#order-count").textContent = `${orders.length} orders`;
  document.querySelector("#orders").innerHTML = orders.map((order) => {
    const margin = ((order.revenue_cents - order.cost_cents) / order.revenue_cents * 100).toFixed(1);
    const tone = order.status === "In production" ? "production" : order.status === "Ready" ? "ready" : "";
    return `<tr><td>${order.reference}</td><td>${order.customer}</td><td>${order.product}</td><td>${order.quantity}</td><td>${order.due_date}</td><td><span class="status ${tone}">${order.status}</span></td><td class="margin">${margin}%</td></tr>`;
  }).join("");
}

document.querySelector("#quote-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget));
  payload.quantity = Number(payload.quantity);
  for (const key of Object.keys(payload)) if (key !== "quantity") payload[key] = Number(payload[key]);
  const result = await api("/api/quotes", { method: "POST", body: JSON.stringify(payload) });
  document.querySelector("#quote-result").innerHTML = `<span>Estimated total</span><strong>${new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD" }).format(result.total_price)}</strong><small>Unit ${result.unit_price.toFixed(2)} · Cost ${result.unit_cost.toFixed(2)} · Risk buffer ${result.risk_buffer.toFixed(2)}</small>`;
});
document.querySelector("#refresh").addEventListener("click", load);
load();
