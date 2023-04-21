from PIL.Image import LANCZOS
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from .constants import FONT, TEMPLATE_PATH, FIRST_TEXT_Y, FONT_SIZE, \
    SECOND_FONT_SIZE, PADDING, FRAME_BOX, SECOND_TEXT_PADDING, \
    SECOND_TEXT_Y


class Frame:
    def __init__(self, x_start: int, y_start: int, x_end: int, y_end: int):
        self.x_start: int = x_start
        self.y_start: int = y_start
        self.x_end: int = x_end
        self.y_end: int = y_end

    @property
    def size(self) -> tuple[int, int]:
        return self.x_end - self.x_start, self.y_end - self.y_start

    @property
    def coords(self) -> tuple[int, int, int, int]:
        return self.x_start, self.y_start, self.x_end, self.y_end


class Template:
    def __init__(self, image, frame, width, height, padding) -> None:
        self.image: Image = image
        self.frame: Frame = frame
        self.width: int = width
        self.height: int = height
        self.padding: int = padding


class Generator:
    def __init__(self, text: str, input: str, output: str, font: str = FONT):
        texts = text.split('\n')
        if len(texts) > 1:
            self.text = texts[0]
            self.text2 = texts[1]
        else:
            self.text = text
            self.text2 = None
        self.font = font
        self.input_image = input
        self.output_image = output

    def generate(self) -> None:
        templ = Image.open(TEMPLATE_PATH).convert("RGB")
        template = Template(
            image=templ,
            width=templ.size[0],
            height=templ.size[1],
            frame=Frame(*FRAME_BOX),
            padding=PADDING,
        )
        input = Image.open(self.input_image).convert("RGB")
        dem_image = input.resize(
            template.frame.size
        )
        template.image.paste(dem_image, box=template.frame.coords)

        new_img = self.__draw_text(template)
        new_img.save(self.output_image)

    def __draw_text(self, template: Template) -> Image:
        draw = ImageDraw.Draw(template.image)
        text_font = ImageFont.truetype(self.font, FONT_SIZE)

        size = int(FONT_SIZE)
        text_width = text_font.getsize(self.text)[0]
        additional = SECOND_TEXT_PADDING if self.text2 is None else 0

        while text_width >= template.width - template.padding * 2:
            text_font = ImageFont.truetype(self.font, size)
            text_width = text_font.getsize(self.text)[0]
            size -= 1
        draw.text(((template.width - text_width) / 2,
                   FIRST_TEXT_Y + additional), self.text,
                  font=text_font, fill='white')

        if self.text2:
            size2 = int(SECOND_FONT_SIZE)
            text_font = ImageFont.truetype(self.font, size2)
            text_width = text_font.getsize(self.text2)[0]

            while text_width >= template.width - template.padding * 2:
                text_font = ImageFont.truetype(self.font, size2)
                text_width = text_font.getsize(self.text2)[0]
                size2 -= 1
            draw.text(((template.width - text_width) / 2, SECOND_TEXT_Y),
                      self.text2, font=text_font, fill='white')

        return template.image
