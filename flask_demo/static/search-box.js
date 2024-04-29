const searchBar = document.querySelector("#search-bar");
const searchBox = document.querySelector(".search-box");
const searchUl = document.querySelector(".search-ul");
let cache = "";



const timer = (beforeInput) => {
    // 0.5초마다 검색어를 확인
    // 하나하나 변경될때마다 데이터를 넘기는 것보다 딜레이가 있는 것이 낫다 판단
    setTimeout(() => {
        if (searchBar.value === beforeInput) {
            loadData(searchBar.value);
            checkInput();
        } else {
            checkInput();
        } // if-else

        // 검색어가 없으면 요소를 숨김
        // if (searchBar.value !== "") {
        //     searchBox.classList.remove("hide");
        // } else {
        //     searchBox.classList.add("hide");
        // }
    }, 300);
} // timer

// 일정 시간 간격으로 조회
const checkInput = () => {
    const beforeInput = searchBar.value;
    timer(beforeInput);
}

// 검색어 불러오기
const loadData = (word) => {
    let url = `/suggest?query=${word}`;

    // 검색어를 입력하면 url 값이 변경된다
    if (cache !== url) {
        cache = url;
        let data = {};

        data.word = word;
        console.log(word); // {word = "축구"}

        fetch(cache)
            // response 객체를 json 변환
            .then((res) => res.json())
            .then((data) => {
                console.log(data);
                fillSearch(data); // data로 list 만드는 함수 실행
            })
            .catch((err) => {
                console.log(err);
            });
    }
}



const fillSearch = (data) => {
    searchUl.innerHTML = "";

    // 데이터 가공하기
    data.forEach((el, idx) => {

        // html 요소 생성
        const li = document.createElement("li");
        li.textContent = el;
        // li.setAttribute("onclick","suggest_click")
        li.onclick = function () {
            suggest_click(el);
        }
        searchUl.appendChild(li);
    })
}

function suggest_click(term) {
    window.location.href = "/search?term="+term;
}

function check_click() {
    checkInput();
    searchBox.classList.remove("hide");
}



// 외부영역 클릭 시 팝업 닫기
$(document).mouseup(function (e){
	var LayerPopup = $(".search-box");
	if(LayerPopup.has(e.target).length === 0){
		LayerPopup.addClass("hide");
	} else {
        LayerPopup.removeClass("hide");
    }
});