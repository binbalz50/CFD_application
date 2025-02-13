from docx import Document
from docx.shared import Inches

class doc:
    def title(self):
        self.text=Document()
        self.text.add_heading("Báo cáo mô hình 3D", level=1)
        self.text.add_paragraph("Hình ảnh của mô hình 3D được tạo bằng PyVista:")  
        self.text.add_picture("mesh.png", width=Inches(4))

        # Lưu file Word
        word_path = "bao_cao.docx"
        self.text.save(word_path)
