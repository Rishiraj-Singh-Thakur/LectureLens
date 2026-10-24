const topicButtons = document.querySelectorAll(".topic-btn");
const searchInput = document.getElementById("search-input");
const searchForm = document.getElementById("search-form");
const loadingOverlay =
    document.getElementById("loading-overlay");
const timer =
    document.getElementById("timer");
searchForm.addEventListener("submit", () => {
    loadingOverlay.style.display = "flex";
    startTimer();

});

topicButtons.forEach((button) => {
    button.addEventListener("click", () => {
        loadingOverlay.style.display="flex";
        startTimer();
        searchInput.value = button.textContent;
        searchForm.submit();
    });

});

// time function
function startTimer(){
    let second = 60;

    timer.textContent = `${second}sec`;
    setInterval(()=>{
        if(second>0){
            second--;
            timer.textContent = `${second} sec`;
        }
    },1000);
}

window.addEventListener("load",() => {
    const answer = document.querySelector(".result-card");

    if(answer){
        setTimeout(() => {
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior : "smooth"
            });
        }, 1000);
    }
})