import os
import torch
from PIL import Image, ImageOps
from diffusers import StableDiffusionInpaintPipeline

def main():
    img_path = r"images\temp01.png"
    output_dir = "output"
    model_dir = "model"
    target_size = 512

    # 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    # 이미지 확인 (없으면 테스트용 임시 이미지 생성)
    if not os.path.exists(img_path):
        print(f"Warning: {img_path} not found. Creating a dummy image for testing.")
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        dummy = Image.new("RGBA", (256, 256), (255, 0, 0, 255))
        dummy.save(img_path)

    print("로컬 모델 로딩 중 (필요시 model/ 에 다운로드됩니다)...")
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        "runwayml/stable-diffusion-inpainting",
        cache_dir=model_dir,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        safety_checker=None
    )

    if torch.cuda.is_available():
        pipe = pipe.to("cuda")
    elif torch.backends.mps.is_available():
        pipe = pipe.to("mps")
    else:
        pipe = pipe.to("cpu")

    print(f"이미지 준비 중: {img_path}")
    original_image = Image.open(img_path).convert("RGBA")
    
    # 512x512 투명 캔버스 생성
    init_image = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))

    # 원본 이미지가 512x512보다 크면 축소
    img_w, img_h = original_image.size
    ratio = min((target_size - 64) / img_w, (target_size - 64) / img_h)
    if ratio < 1.0:
        new_w, new_h = int(img_w * ratio), int(img_h * ratio)
        original_image = original_image.resize((new_w, new_h), Image.LANCZOS)
    else:
        new_w, new_h = img_w, img_h

    # 중앙 배치
    offset_x = (target_size - new_w) // 2
    offset_y = (target_size - new_h) // 2
    init_image.paste(original_image, (offset_x, offset_y), original_image)

    # RGB로 변환 (SD는 RGB 사용)
    init_image_rgb = Image.new("RGB", (target_size, target_size), (255, 255, 255))
    init_image_rgb.paste(init_image, mask=init_image.split()[3])

    # 마스크 이미지 생성: Alpha 채널을 반전시킴 (투명한 배경=흰색=인페인트 영역)
    alpha = init_image.split()[3]
    mask_image = ImageOps.invert(alpha)

    prompt = "high quality, seamless background extension, highly detailed, realistic scenery"
    negative_prompt = "low resolution, ugly, blurry, borders, edges, artifacts"

    print("아웃페인트(Inpaint) 생성 시작...")
    result_image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=init_image_rgb,
        mask_image=mask_image,
        num_inference_steps=20,
        guidance_scale=7.5
    ).images[0]

    output_path = os.path.join(output_dir, "output.png")
    result_image.save(output_path)
    print(f"완료! 결과물이 저장되었습니다: {output_path}")

if __name__ == "__main__":
    main()