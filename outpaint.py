import os
import torch
from PIL import Image, ImageOps
from diffusers import StableDiffusionInpaintPipeline

class Outpainter:
    def __init__(self, model_dir="model"):
        self.model_dir = model_dir
        self.pipe = None
        
    def load_model(self):
        if self.pipe is not None:
            return
            
        print("로컬 AI 모델 로딩 중 (최초 실행 시 시간이 걸릴 수 있습니다)...")
        # 모델 캐시 경로 보장
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            cache_dir=self.model_dir,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            safety_checker=None
        )

        # 하드웨어 가속 설정
        if torch.cuda.is_available():
            self.pipe = self.pipe.to("cuda")
        elif torch.backends.mps.is_available():
            self.pipe = self.pipe.to("mps")
        else:
            self.pipe = self.pipe.to("cpu")
            
        print("모델 로딩 완료.")

    def run(self, img_path, output_path=None, prompt=None):
        self.load_model()
        
        if not os.path.exists(img_path):
            print(f"Error: {img_path} 파일을 찾을 수 없습니다.")
            return None

        # 이미지 로드 및 RGBA 변환
        img = Image.open(img_path).convert("RGBA")
        width, height = img.size
        
        # Stable Diffusion 모델은 가로세로가 8의 배수여야 합니다.
        gen_w = (width // 8) * 8
        gen_h = (height // 8) * 8
        
        if gen_w != width or gen_h != height:
            print(f"해상도 조정: {width}x{height} -> {gen_w}x{gen_h}")
            img = img.resize((gen_w, gen_h), Image.LANCZOS)
            width, height = gen_w, gen_h

        # 1. 원본 이미지를 흰색 배경의 RGB 이미지로 변환 (SD 인페인트 입력용)
        init_image_rgb = Image.new("RGB", (width, height), (255, 255, 255))
        # 알파 채널을 마스크로 사용하여 투명하지 않은 부분만 붙여넣기
        init_image_rgb.paste(img, mask=img.split()[3])

        # 2. 마스크 이미지 생성 (투명한 영역 = 칠해야 할 곳 = 흰색)
        alpha = img.split()[3]
        mask_image = ImageOps.invert(alpha)

        # 3. 프롬프트 설정
        if prompt is None:
            prompt = "high quality, seamless background extension, highly detailed, realistic scenery"
        negative_prompt = "low resolution, ugly, blurry, borders, edges, artifacts, text, watermark"

        print(f"아웃페인트 생성 시작 (크기: {width}x{height})...")
        # 생성 실행
        result_image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=init_image_rgb,
            mask_image=mask_image,
            num_inference_steps=20,
            guidance_scale=7.5
        ).images[0]

        # 4. 결과 저장
        if output_path:
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            result_image.save(output_path)
            print(f"결과 저장 완료: {output_path}")
            
        return result_image

# 외부 파일에서 간편하게 호출하기 위한 함수
_painter_instance = None

def apply_outpaint(img_path, output_path=None, prompt=None):
    global _painter_instance
    if _painter_instance is None:
        _painter_instance = Outpainter()
    return _painter_instance.run(img_path, output_path, prompt)

if __name__ == "__main__":
    # 테스트 실행
    test_img = r"images\temp01.png"
    if os.path.exists(test_img):
        apply_outpaint(test_img, r"output\test_function_result.png")
    else:
        print("테스트할 이미지가 없습니다. images\\temp01.png 를 확인해 주세요.")