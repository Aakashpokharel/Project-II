const dough = document.getElementById("dough"),
  pie = document.getElementById("pie"),
  bar = document.getElementById("bar"),
  polarArea = document.getElementById("polarArea"),
  today = document.getElementById("today"),
  week = document.getElementById("week"),
  month = document.getElementById("month"),
  year = document.getElementById("year");
let myChart, data, labels, type, label_title;
dough.addEventListener("click", () => {
  myChart.destroy(), renderChart(data, labels, "doughnut", label_title);
}),
  pie.addEventListener("click", () => {
    myChart.destroy(), renderChart(data, labels, "pie", label_title);
  }),
  bar.addEventListener("click", () => {
    myChart.destroy(), renderChart(data, labels, "bar", label_title);
  }),
  polarArea.addEventListener("click", () => {
    myChart.destroy(), renderChart(data, labels, "polarArea", label_title);
  }),
  today.addEventListener("click", () => {
    myChart.destroy(), getChartData("bar", "today");
  }),
  week.addEventListener("click", () => {
    myChart.destroy(), getChartData("bar", "week");
  }),
  month.addEventListener("click", () => {
    myChart.destroy(), getChartData("bar", "month");
  }),
  year.addEventListener("click", () => {
    myChart.destroy(), getChartData("bar", "year");
  });
const renderChart = (e, t, a, r) => {
    var d = document.getElementById("myChart").getContext("2d");
    myChart = new Chart(d, {
      type: a,
      data: {
        labels: t,
        datasets: [
          {
            label: r,
            data: e,
            backgroundColor: [
              "rgba(255, 99, 132, 0.2)",
              "rgba(54, 162, 235, 0.2)",
              "rgba(255, 206, 86, 0.2)",
              "rgba(75, 192, 192, 0.2)",
              "rgba(153, 102, 255, 0.2)",
              "rgba(255, 159, 64, 0.2)",
            ],
            borderColor: [
              "rgba(255, 99, 132, 1)",
              "rgba(54, 162, 235, 1)",
              "rgba(255, 206, 86, 1)",
              "rgba(75, 192, 192, 1)",
              "rgba(153, 102, 255, 1)",
              "rgba(255, 159, 64, 1)",
            ],
            borderWidth: 1,
          },
        ],
      },
      options: { title: { display: !0, text: r } },
    });
  },
  getChartData = (e, t) => {
    fetch(`/income/income-summary-data?filter=${t}`)
      .then((e) => e.json())
      .then((t) => {
        const a = t.income_source_data;
        label_title = t.label_title;
        const [r, d] = [Object.keys(a), Object.values(a)];
        (labels = r), (data = d), renderChart(d, r, e, label_title);
      });
  };
document.onload = getChartData("pie", "today");
