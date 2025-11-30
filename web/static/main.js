document.getElementById("reviewForm").onsubmit = async (e) => {
    e.preventDefault();

    const form = new FormData(e.target);

    const response = await fetch("/review", {
        method: "POST",
        body: form
    });

    const data = await response.json();

    document.getElementById("output").textContent =
        JSON.stringify(data, null, 4);
};

document.getElementById("copyJsonBtn").onclick = () => {
    const jsonText = document.getElementById("output").textContent;
    navigator.clipboard.writeText(jsonText);
    alert("JSON copied to clipboard!");
};
