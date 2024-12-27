// 전역 변수
let songs = [];
let lyricsData = {};

// 노래 추가 함수
function addSong() {
    const input = document.getElementById('songInput');
    if (input.value.trim()) {
        songs.unshift(input.value.trim());  // 큐 방식으로 추가
        updateSongList();
        input.value = '';
    }
}

// 노래 목록 업데이트
function updateSongList() {
    const list = document.getElementById('songList');
    list.innerHTML = songs.map((song, index) => `
        <div class="flex items-center gap-2">
            <span class="flex-1 p-2 bg-gray-50 rounded">${song}</span>
            <button onclick="removeSong(${index})" 
                    class="text-red-500 hover:text-red-600">삭제</button>
        </div>
    `).join('');
}

// 노래 삭제
function removeSong(index) {
    songs.splice(index, 1);
    updateSongList();
}

// 가사 검색
async function searchLyrics() {
    if (songs.length === 0) {
        alert('찬양을 먼저 추가해주세요.');
        return;
    }

    const results = document.getElementById('results');
    results.innerHTML = '<div class="text-center">검색중...</div>';

    try {
        const response = await fetch('/search_lyrics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ songs: songs })
        });

        lyricsData = await response.json();
        displayResults();
        updateSortableList();
        document.getElementById('pptSection').classList.remove('hidden');
    } catch (error) {
        results.innerHTML = '<div class="text-red-500">오류가 발생했습니다.</div>';
    }
}

// 검색 결과 표시
function displayResults() {
    const results = document.getElementById('results');
    results.innerHTML = Object.entries(lyricsData).map(([song, data], index) => `
        <div class="song-container p-4 border rounded">
            <div class="flex items-center justify-between mb-2">
                <h3 class="text-xl font-semibold editable-title" 
                    onclick="makeEditable(this)" 
                    data-original-title="${song}">${song}</h3>
                ${data.url ? 
                    `<a href="${data.url}" target="_blank" 
                        class="text-blue-500 hover:text-blue-600">
                        Bugs에서 보기
                    </a>` : 
                    ''}
            </div>
            <textarea class="lyrics-editor w-full p-2 border rounded" 
                    onchange="updateLyrics('${song}', this.value)">${data.lyrics || '가사 정보를 불러올 수 없습니다.'}</textarea>
        </div>
    `).join('');
}

// 제목 수정 가능하게 만들기
function makeEditable(element) {
    const originalTitle = element.textContent;
    const input = document.createElement('input');
    input.value = originalTitle;
    input.className = 'text-xl font-semibold p-1 border rounded';
    
    input.onblur = function() {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== originalTitle) {
            const oldTitle = element.dataset.originalTitle;
            lyricsData[newTitle] = lyricsData[oldTitle];
            delete lyricsData[oldTitle];
            element.textContent = newTitle;
            element.dataset.originalTitle = newTitle;
            updateSortableList();
        } else {
            element.textContent = originalTitle;
        }
    };
    
    input.onkeypress = function(e) {
        if (e.key === 'Enter') {
            input.blur();
        }
    };
    
    element.textContent = '';
    element.appendChild(input);
    input.focus();
}

// 가사 업데이트
function updateLyrics(song, newLyrics) {
    lyricsData[song].lyrics = newLyrics;
    updateSortableList();
}

// 정렬 가능한 목록 업데이트
function updateSortableList() {
    const sortableResults = document.getElementById('sortableResults');
    sortableResults.innerHTML = Object.keys(lyricsData).map((song, index) => `
        <div class="p-3 bg-white border rounded shadow-sm flex items-center gap-4" data-id="${index}">
            <span class="sortable-handle cursor-move">⋮⋮</span>
            <span>${song}</span>
        </div>
    `).join('');

    new Sortable(sortableResults, {
        animation: 150,
        handle: '.sortable-handle'
    });
}

// PPT 생성
async function createPPT() {
    const sortableResults = document.getElementById('sortableResults');
    const songOrder = Array.from(sortableResults.children).map(el => {
        const title = el.querySelector('span:last-child').textContent;
        return {
            title: title,
            lyrics: lyricsData[title]?.lyrics || "가사 정보를 불러올 수 없습니다."  // lyrics가 없다면 기본값 설정
        };
    });

    try {
        const response = await fetch('/create_ppt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ songOrder: songOrder })
        });

        const result = await response.json();
        if (result.success) {
            window.location.href = result.path;
        }
    } catch (error) {
        alert('PPT 생성 중 오류가 발생했습니다.');
    }
}

// 엔터키로 노래 추가
document.getElementById('songInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        addSong();
    }
});
