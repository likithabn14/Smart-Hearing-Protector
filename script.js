const enabled = document.getElementById("enabled");
const threshold = document.getElementById("threshold");
const safeLevel = document.getElementById("safeLevel");

const thresholdValue = document.getElementById("thresholdValue");
const safeValue = document.getElementById("safeValue");

const meterFill = document.getElementById("meterFill");
const peakText = document.getElementById("peakText");

// Update text beside sliders
threshold.addEventListener("input", () => {
    thresholdValue.innerText = threshold.value + "%";
    sendSettings();
});

safeLevel.addEventListener("input", () => {
    safeValue.innerText = safeLevel.value + "%";
    sendSettings();
});

// Toggle protection
enabled.addEventListener("change", () => {
    sendSettings();
});

// Send settings to Flask
function sendSettings() {
    fetch("/update_settings", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            enabled: enabled.checked,
            threshold: threshold.value,
            safe_level: safeLevel.value
        })
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(err => console.error(err));
}

// Get live audio peak every 100ms
function updatePeak() {
    fetch("/get_live_data")
        .then(response => response.json())
        .then(data => {

            let peak = Math.round(data.peak * 100);

            meterFill.style.width = peak + "%";
            peakText.innerHTML = peak + "%";

        })
        .catch(err => console.log(err));
}

setInterval(updatePeak, 100);

// Send default settings when page loads
sendSettings();