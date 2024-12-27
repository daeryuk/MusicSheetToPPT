from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import os
import re
import webbrowser
from threading import Timer

app = Flask(__name__)

def clean_lyrics(lyrics):
    # 불필요한 문자 및 패턴 제거
    cleaned = lyrics.replace('_x000D_', '\n')  # _x000D_ 를 줄바꿈으로 변환
    cleaned = re.sub(r'^[•●■□○\-\*]\s*', '', cleaned, flags=re.MULTILINE)  # 글머리 기호 제거
    cleaned = re.sub(r'\s*×\d+\s*', '', cleaned)  # ×2, ×3 등의 반복 표시 제거
    cleaned = re.sub(r'[.]{3,}', '', cleaned)  # 점(...) 제거
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # 3개 이상의 연속된 줄바꿈을 2개로 통일
    
    # 빈 줄만 있는 라인 제거
    lines = [line for line in cleaned.split('\n') if line.strip()]
    cleaned = '\n'.join(lines)
    
    # 시작과 끝의 불필요한 공백 제거
    cleaned = cleaned.strip()
    
    return cleaned

def search_lyrics(song_title):
    search_url = f"https://music.bugs.co.kr/search/track?q={song_title}"
    
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        track_info = soup.find('a', {'class': 'trackInfo'})
        if not track_info:
            return None, None
            
        song_url = track_info['href']
        song_page = requests.get(song_url)
        song_soup = BeautifulSoup(song_page.text, 'html.parser')
        
        lyrics_container = song_soup.find('div', {'class': 'lyricsContainer'})
        if lyrics_container and lyrics_container.find('xmp'):
            lyrics = lyrics_container.find('xmp').text.strip()
            # 가사 전처리 적용
            lyrics = clean_lyrics(lyrics)
            return lyrics, song_url
        return None, None
    except:
        return None, None

def create_ppt(lyrics_dict, song_order):
    prs = Presentation()
    
    for song_idx in song_order:
        song_title = song_idx['title']
        lyrics = lyrics_dict[song_title]
        
        # 제목 전용 슬라이드 생성
        title_slide = prs.slides.add_slide(prs.slide_layouts[0])  # 제목 슬라이드 레이아웃 사용
        title = title_slide.shapes.title
        title.text = song_title
        
        # 제목 슬라이드 스타일링
        for paragraph in title.text_frame.paragraphs:
            paragraph.alignment = PP_ALIGN.CENTER
            paragraph.font.size = Pt(44)

        # 의미 있는 줄바꿈을 기준으로 문단 나누기
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', lyrics.strip()) if p.strip()]
        
        # 모든 문단을 새로운 슬라이드에 추가
        for paragraph in paragraphs:
            if paragraph.strip():  # 빈 문단 건너뛰기
                content_slide = prs.slides.add_slide(prs.slide_layouts[5])  # 빈 레이아웃 사용
                
                # 가사를 위한 텍스트박스 추가
                text_box = content_slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(6))
                text_frame = text_box.text_frame
                text_frame.text = paragraph
                
                # 가사 텍스트 스타일링
                for para in text_frame.paragraphs:
                    para.alignment = PP_ALIGN.CENTER
                    para.font.size = Pt(32)
    
    output_path = "static/output.pptx"
    prs.save(output_path)
    return output_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_lyrics', methods=['POST'])
def process_lyrics():
    songs = request.json['songs']
    results = {}
    
    for song in songs:
        lyrics, song_url = search_lyrics(song)
        if lyrics:
            results[song] = {
                'lyrics': lyrics,
                'url': song_url
            }
        else:
            results[song] = {
                'lyrics': "가사를 찾을 수 없습니다.",
                'url': None
            }
    
    return jsonify(results)

@app.route('/create_ppt', methods=['POST'])
def generate_ppt():
    data = request.json
    lyrics_dict = {song['title']: song['lyrics'] for song in data['songOrder']}
    ppt_path = create_ppt(lyrics_dict, data['songOrder'])
    return jsonify({'success': True, 'path': ppt_path})

def open_browser():
    try:
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
        webbrowser.get('chrome').open_new("http://127.0.0.1:5000/")
    except Exception as e:
        print(f"Chrome 브라우저를 열 수 없습니다: {e}")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=True)