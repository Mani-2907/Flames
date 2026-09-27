const form = document.getElementById("flamesForm");
const resultArea = document.getElementById("resultArea");
const resultNames = document.getElementById("resultNames");
const resultValue = document.getElementById("resultValue");
const resultExplanation = document.getElementById("resultExplanation");
const resultError = document.getElementById("resultError");
const resultSaveStatus = document.getElementById("resultSaveStatus");
const submitButton = form.querySelector("button[type='submit']");

const relationshipAudio = {
    F: [392, 523.25, 659.25],
    L: [440, 554.37, 659.25, 783.99],
    A: [349.23, 392, 440, 523.25],
    M: [392, 440, 493.88, 587.33],
    E: [220, 293.66, 349.23, 293.66],
    S: [261.63, 329.63, 392, 523.25],
};

function playRelationshipTone(code) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    const ctx = new AudioContextClass();
    const notes = relationshipAudio[code] || relationshipAudio.F;
    const now = ctx.currentTime;

    notes.forEach((frequency, index) => {
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.type = index % 2 === 0 ? "sine" : "triangle";
        oscillator.frequency.setValueAtTime(frequency, now + index * 0.18);
        gainNode.gain.setValueAtTime(0.0001, now + index * 0.18);
        gainNode.gain.exponentialRampToValueAtTime(0.12, now + index * 0.18 + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.0001, now + index * 0.18 + 0.32);

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        oscillator.start(now + index * 0.18);
        oscillator.stop(now + index * 0.18 + 0.34);
    });

    setTimeout(() => ctx.close(), 900);
}

function playErrorTone() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    const ctx = new AudioContextClass();
    const now = ctx.currentTime;

    [220, 180].forEach((frequency, index) => {
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.type = "sawtooth";
        oscillator.frequency.setValueAtTime(frequency, now + index * 0.18);
        gainNode.gain.setValueAtTime(0.0001, now + index * 0.18);
        gainNode.gain.exponentialRampToValueAtTime(0.08, now + index * 0.18 + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.0001, now + index * 0.18 + 0.22);

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        oscillator.start(now + index * 0.18);
        oscillator.stop(now + index * 0.18 + 0.26);
    });

    setTimeout(() => ctx.close(), 600);
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const firstName = document.getElementById("name1").value.trim();
    const secondName = document.getElementById("name2").value.trim();
    resultError.hidden = true;
    submitButton.disabled = true;
    submitButton.innerHTML = "<span>Calculating...</span>";

    try {
        const response = await fetch("/api/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name1: firstName, name2: secondName })
        });
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to calculate the result.");
        }

        resultNames.textContent = `${result.name1} + ${result.name2}`;
        resultValue.textContent = result.relationship;
        resultExplanation.textContent = result.explanation;
        resultSaveStatus.textContent = "";
        resultArea.hidden = false;
        playRelationshipTone(result.code);
    } catch (error) {
        resultNames.textContent = "";
        resultValue.textContent = "";
        resultExplanation.textContent = "";
        resultSaveStatus.textContent = "";
        resultError.textContent = error.message;
        resultError.hidden = false;
        resultArea.hidden = false;
        playErrorTone();
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = "<span>Find Relationship</span>";
    }
});
