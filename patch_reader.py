import re

with open('templates/reader/reader.html', 'r') as f:
    content = f.read()

# Replace page-num span with an input and add bookmark button
content = content.replace(
    '<span id="page-num">1</span> / <span id="page-count">-</span>',
    '<input type="number" id="page-input" value="1" min="1" style="width:50px; background:transparent; color:var(--fg); border:1px solid var(--border-dark); border-radius:4px; text-align:center;"> / <span id="page-count">-</span>'
)

content = content.replace(
    '<button id="next-btn" class="nav-btn">NEXT &rarr;</button>',
    '<button id="next-btn" class="nav-btn">NEXT &rarr;</button>\n                        <button id="bookmark-btn" class="nav-btn" style="margin-left: 8px;" title="Bookmark this page">🔖 Save</button>'
)

# Update pageNumEl to pageInputEl
content = content.replace(
    "const pageNumEl = document.getElementById('page-num');",
    "const pageInputEl = document.getElementById('page-input');\n        const bookmarkBtn = document.getElementById('bookmark-btn');\n\n        pageInputEl.addEventListener('change', (e) => {\n            let num = parseInt(e.target.value);\n            if (num > 0 && num <= pdfDoc.numPages) {\n                pageNum = num;\n                queueRenderPage(pageNum);\n            } else {\n                e.target.value = pageNum;\n            }\n        });\n\n        bookmarkBtn.addEventListener('click', () => {\n            localStorage.setItem('anuvad_book_' + bookId + '_bookmark', pageNum);\n            alert('Page ' + pageNum + ' bookmarked!');\n        });"
)

content = content.replace(
    "pageNumEl.textContent = num;",
    "pageInputEl.value = num;"
)

# Update watermark regex logic
old_watermark = """                    // If the remaining text is completely empty or just a number (like page '1'), 
                    // then this entire block is a header/footer watermark.
                    if (/^\\d*$/.test(textWithoutUrl)) {
                        return '';
                    }"""

new_watermark = """                    if (p.toLowerCase().includes('hindustanbooks.com')) {
                        return '';
                    }
                    // If the remaining text is completely empty or just a number (like page '1'), 
                    // then this entire block is a header/footer watermark.
                    if (/^\\s*\\d*\\s*$/.test(textWithoutUrl)) {
                        return '';
                    }"""

content = content.replace(old_watermark, new_watermark)

with open('templates/reader/reader.html', 'w') as f:
    f.write(content)
