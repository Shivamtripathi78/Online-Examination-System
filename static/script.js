const examForm = document.getElementById("examForm");
const timerElement = document.getElementById("timer");

if (examForm && timerElement) {
    let remainingTime = 10 * 60;
    let submitted = false;

    function submitExam() {
        if (submitted) return;

        submitted = true;
        examForm.submit();
    }

    function updateTimer() {
        const minutes = Math.floor(remainingTime / 60);
        const seconds = remainingTime % 60;

        timerElement.textContent =
            `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

        if (remainingTime <= 0) {
            timerElement.textContent = "00:00";
            submitExam();
            return;
        }

        remainingTime--;
    }

    examForm.addEventListener("submit", function (event) {
        if (submitted) return;

        const confirmed = confirm(
            "Are you sure you want to submit your examination?"
        );

        if (!confirmed) {
            event.preventDefault();
        } else {
            submitted = true;
        }
    });

    updateTimer();
    setInterval(updateTimer, 1000);
}