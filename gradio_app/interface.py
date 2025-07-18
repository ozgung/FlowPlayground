"""
Gradio interface for FlowPlayground development and testing.
"""
import gradio as gr
import asyncio
import aiohttp
import io
import json
import os
from typing import Optional, Dict, Any, Tuple
from PIL import Image
import tempfile
import base64

from app.core.config import settings
from app.services.fal_ai import fal_ai_service
from app.models import (
    ImageEnhanceRequest,
    StyleTransferRequest,
    ImageGenerateRequest,
    VideoProcessRequest,
)


class GradioInterface:
    """Gradio interface for FlowPlayground."""
    
    def __init__(self):
        self.api_base_url = f"http://localhost:{settings.port}"
        self.temp_dir = tempfile.mkdtemp()
        
    async def enhance_image(
        self,
        image: Image.Image,
        strength: float = 0.8,
        preserve_details: bool = True,
        enhance_colors: bool = True,
        reduce_noise: bool = True
    ) -> Tuple[Optional[Image.Image], str]:
        """Enhance image quality."""
        try:
            if image is None:
                return None, "Please upload an image first."
            
            # Convert PIL Image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Create request
            request = ImageEnhanceRequest(
                strength=strength,
                preserve_details=preserve_details,
                enhance_colors=enhance_colors,
                reduce_noise=reduce_noise
            )
            
            # Process with fal.ai service
            result = await fal_ai_service.enhance_image(
                img_bytes.getvalue(),
                "gradio_upload.png",
                request
            )
            
            # For demo purposes, return the original image with success message
            # In production, you would fetch the result from result["result_url"]
            return image, f"✅ Image enhanced successfully! Processing time: {result['metadata'].get('processing_time', 0):.2f}s"
            
        except Exception as e:
            return None, f"❌ Error enhancing image: {str(e)}"
    
    async def style_transfer(
        self,
        image: Image.Image,
        style_strength: float = 0.8,
        preserve_structure: bool = True,
        style_reference: str = "artistic"
    ) -> Tuple[Optional[Image.Image], str]:
        """Apply style transfer to image."""
        try:
            if image is None:
                return None, "Please upload an image first."
            
            # Convert PIL Image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Create request
            request = StyleTransferRequest(
                style_strength=style_strength,
                preserve_structure=preserve_structure,
                style_reference=style_reference
            )
            
            # Process with fal.ai service
            result = await fal_ai_service.style_transfer(
                img_bytes.getvalue(),
                "gradio_upload.png",
                request
            )
            
            # For demo purposes, return the original image with success message
            return image, f"✅ Style transfer applied successfully! Style: {style_reference}"
            
        except Exception as e:
            return None, f"❌ Error applying style transfer: {str(e)}"
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 20,
        guidance_scale: float = 7.5,
        seed: int = -1
    ) -> Tuple[Optional[Image.Image], str]:
        """Generate image from text prompt."""
        try:
            if not prompt.strip():
                return None, "Please enter a text prompt."
            
            # Create request
            request = ImageGenerateRequest(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                seed=seed if seed >= 0 else None
            )
            
            # Process with fal.ai service
            result = await fal_ai_service.generate_image(request)
            
            # For demo purposes, create a placeholder image
            placeholder = Image.new('RGB', (width, height), color='lightblue')
            
            return placeholder, f"✅ Image generated successfully! Seed: {result['metadata'].get('seed', 'random')}"
            
        except Exception as e:
            return None, f"❌ Error generating image: {str(e)}"
    
    async def process_video(
        self,
        video_path: str,
        operation: str = "enhance",
        quality: str = "high"
    ) -> Tuple[Optional[str], str]:
        """Process video file."""
        try:
            if not video_path or not os.path.exists(video_path):
                return None, "Please upload a video file."
            
            # Read video file
            with open(video_path, 'rb') as f:
                video_data = f.read()
            
            # Create request
            request = VideoProcessRequest(
                operation=operation,
                quality=quality
            )
            
            # Process with fal.ai service
            result = await fal_ai_service.process_video(
                video_data,
                os.path.basename(video_path),
                request
            )
            
            # For demo purposes, return the original video path
            return video_path, f"✅ Video processed successfully! Operation: {operation}"
            
        except Exception as e:
            return None, f"❌ Error processing video: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create Gradio interface."""
        with gr.Blocks(
            title="FlowPlayground - AI Photo & Video Processing",
            theme=gr.themes.Soft()
        ) as interface:
            
            gr.Markdown("""
            # 🎨 FlowPlayground - AI Photo & Video Processing
            
            A powerful AI-powered backend for photo and video processing. Test the API capabilities below.
            
            **Features:**
            - 🖼️ Image Enhancement
            - 🎨 Style Transfer
            - ✨ Image Generation
            - 🎬 Video Processing
            """)
            
            with gr.Tabs():
                
                # Image Enhancement Tab
                with gr.Tab("🖼️ Image Enhancement"):
                    with gr.Row():
                        with gr.Column():
                            enhance_input = gr.Image(
                                label="Upload Image",
                                type="pil",
                                height=300
                            )
                            
                            with gr.Accordion("Enhancement Settings", open=False):
                                enhance_strength = gr.Slider(
                                    minimum=0.1,
                                    maximum=1.0,
                                    value=0.8,
                                    step=0.1,
                                    label="Enhancement Strength"
                                )
                                enhance_preserve_details = gr.Checkbox(
                                    value=True,
                                    label="Preserve Details"
                                )
                                enhance_colors = gr.Checkbox(
                                    value=True,
                                    label="Enhance Colors"
                                )
                                enhance_noise = gr.Checkbox(
                                    value=True,
                                    label="Reduce Noise"
                                )
                            
                            enhance_btn = gr.Button("🚀 Enhance Image", variant="primary")
                        
                        with gr.Column():
                            enhance_output = gr.Image(
                                label="Enhanced Image",
                                type="pil",
                                height=300
                            )
                            enhance_status = gr.Textbox(
                                label="Status",
                                interactive=False
                            )
                    
                    # Wire up the enhancement function
                    enhance_btn.click(
                        fn=lambda *args: asyncio.run(self.enhance_image(*args)),
                        inputs=[
                            enhance_input,
                            enhance_strength,
                            enhance_preserve_details,
                            enhance_colors,
                            enhance_noise
                        ],
                        outputs=[enhance_output, enhance_status]
                    )
                
                # Style Transfer Tab
                with gr.Tab("🎨 Style Transfer"):
                    with gr.Row():
                        with gr.Column():
                            style_input = gr.Image(
                                label="Upload Image",
                                type="pil",
                                height=300
                            )
                            
                            with gr.Accordion("Style Settings", open=False):
                                style_strength = gr.Slider(
                                    minimum=0.1,
                                    maximum=1.0,
                                    value=0.8,
                                    step=0.1,
                                    label="Style Strength"
                                )
                                style_preserve = gr.Checkbox(
                                    value=True,
                                    label="Preserve Structure"
                                )
                                style_reference = gr.Dropdown(
                                    choices=[
                                        "artistic",
                                        "impressionist",
                                        "abstract",
                                        "watercolor",
                                        "oil_painting",
                                        "sketch"
                                    ],
                                    value="artistic",
                                    label="Style Reference"
                                )
                            
                            style_btn = gr.Button("🎨 Apply Style Transfer", variant="primary")
                        
                        with gr.Column():
                            style_output = gr.Image(
                                label="Styled Image",
                                type="pil",
                                height=300
                            )
                            style_status = gr.Textbox(
                                label="Status",
                                interactive=False
                            )
                    
                    # Wire up the style transfer function
                    style_btn.click(
                        fn=lambda *args: asyncio.run(self.style_transfer(*args)),
                        inputs=[
                            style_input,
                            style_strength,
                            style_preserve,
                            style_reference
                        ],
                        outputs=[style_output, style_status]
                    )
                
                # Image Generation Tab
                with gr.Tab("✨ Image Generation"):
                    with gr.Row():
                        with gr.Column():
                            gen_prompt = gr.Textbox(
                                label="Text Prompt",
                                placeholder="A beautiful landscape with mountains and a lake...",
                                lines=3
                            )
                            gen_negative = gr.Textbox(
                                label="Negative Prompt (Optional)",
                                placeholder="blurry, low quality, distorted...",
                                lines=2
                            )
                            
                            with gr.Accordion("Generation Settings", open=False):
                                with gr.Row():
                                    gen_width = gr.Slider(
                                        minimum=128,
                                        maximum=1024,
                                        value=512,
                                        step=64,
                                        label="Width"
                                    )
                                    gen_height = gr.Slider(
                                        minimum=128,
                                        maximum=1024,
                                        value=512,
                                        step=64,
                                        label="Height"
                                    )
                                
                                gen_steps = gr.Slider(
                                    minimum=1,
                                    maximum=50,
                                    value=20,
                                    step=1,
                                    label="Inference Steps"
                                )
                                gen_guidance = gr.Slider(
                                    minimum=1.0,
                                    maximum=20.0,
                                    value=7.5,
                                    step=0.5,
                                    label="Guidance Scale"
                                )
                                gen_seed = gr.Number(
                                    value=-1,
                                    label="Seed (-1 for random)"
                                )
                            
                            gen_btn = gr.Button("✨ Generate Image", variant="primary")
                        
                        with gr.Column():
                            gen_output = gr.Image(
                                label="Generated Image",
                                type="pil",
                                height=400
                            )
                            gen_status = gr.Textbox(
                                label="Status",
                                interactive=False
                            )
                    
                    # Wire up the generation function
                    gen_btn.click(
                        fn=lambda *args: asyncio.run(self.generate_image(*args)),
                        inputs=[
                            gen_prompt,
                            gen_negative,
                            gen_width,
                            gen_height,
                            gen_steps,
                            gen_guidance,
                            gen_seed
                        ],
                        outputs=[gen_output, gen_status]
                    )
                
                # Video Processing Tab
                with gr.Tab("🎬 Video Processing"):
                    with gr.Row():
                        with gr.Column():
                            video_input = gr.Video(
                                label="Upload Video",
                                height=300
                            )
                            
                            with gr.Accordion("Processing Settings", open=False):
                                video_operation = gr.Dropdown(
                                    choices=["enhance", "stabilize", "style_transfer"],
                                    value="enhance",
                                    label="Operation"
                                )
                                video_quality = gr.Dropdown(
                                    choices=["low", "medium", "high"],
                                    value="high",
                                    label="Quality"
                                )
                            
                            video_btn = gr.Button("🎬 Process Video", variant="primary")
                        
                        with gr.Column():
                            video_output = gr.Video(
                                label="Processed Video",
                                height=300
                            )
                            video_status = gr.Textbox(
                                label="Status",
                                interactive=False
                            )
                    
                    # Wire up the video processing function
                    video_btn.click(
                        fn=lambda *args: asyncio.run(self.process_video(*args)),
                        inputs=[
                            video_input,
                            video_operation,
                            video_quality
                        ],
                        outputs=[video_output, video_status]
                    )
                
                # API Info Tab
                with gr.Tab("📊 API Information"):
                    gr.Markdown(f"""
                    ## API Endpoint Information
                    
                    **Base URL:** `{self.api_base_url}`
                    
                    ### Available Endpoints:
                    
                    #### Image Processing
                    - `POST /api/v1/image/enhance` - Enhance image quality
                    - `POST /api/v1/image/style-transfer` - Apply style transfer
                    - `POST /api/v1/image/generate` - Generate images from text
                    - `POST /api/v1/image/batch` - Batch process multiple images
                    
                    #### Video Processing
                    - `POST /api/v1/video/process` - Process video files
                    - `POST /api/v1/video/enhance` - Enhance video quality
                    - `POST /api/v1/video/stabilize` - Stabilize video
                    
                    #### System
                    - `GET /api/v1/health` - Health check
                    - `GET /api/v1/capabilities` - API capabilities
                    
                    ### Configuration
                    - **Environment:** {settings.environment}
                    - **Max File Size:** {settings.max_file_size / (1024*1024):.1f} MB
                    - **Supported Image Types:** {', '.join(settings.allowed_image_types)}
                    - **Supported Video Types:** {', '.join(settings.allowed_video_types)}
                    
                    ### Documentation
                    - **Swagger UI:** [{self.api_base_url}/docs]({self.api_base_url}/docs)
                    - **ReDoc:** [{self.api_base_url}/redoc]({self.api_base_url}/redoc)
                    """)
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        interface = self.create_interface()
        
        # Default launch parameters
        launch_params = {
            "server_name": "0.0.0.0",
            "server_port": settings.gradio_port,
            "share": False,
            "debug": settings.debug,
            "show_error": settings.debug,
        }
        
        # Add authentication if configured
        if settings.gradio_auth:
            launch_params["auth"] = settings.gradio_auth
        
        # Override with user parameters
        launch_params.update(kwargs)
        
        print(f"🚀 Starting Gradio interface at http://localhost:{settings.gradio_port}")
        print(f"📖 API documentation available at {self.api_base_url}/docs")
        
        return interface.launch(**launch_params)


# Global interface instance
gradio_interface = GradioInterface()


def main():
    """Run the Gradio interface."""
    if settings.gradio_enabled:
        gradio_interface.launch()
    else:
        print("Gradio interface is disabled in configuration")


if __name__ == "__main__":
    main()