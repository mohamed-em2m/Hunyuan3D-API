import gradio as gr
import torch
import trimesh
import tempfile
import os
from PIL import Image
import numpy as np

# Import your 3D generation pipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

# Initialize the pipeline
print("Loading Hunyuan3D pipeline...")
pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2')
print("Pipeline loaded successfully!")

def generate_3d_mesh(image, num_inference_steps, guidance_scale, box_v, octree_resolution,
                    mc_level, num_chunks, eta, enable_pbar, scale_x, scale_y, scale_z,
                    maintain_aspect_ratio, target_width, target_height, target_depth):
    """
    Generate 3D mesh from uploaded image with custom parameters
    """
    if image is None:
        return None, "Please upload an image first."

    try:
        # Update status
        status_msg = f"🔄 Generating 3D mesh with {num_inference_steps} steps..."

        # Generate mesh using the pipeline with custom parameters
        mesh = pipeline(
            image=image,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            box_v=box_v,
            octree_resolution=octree_resolution,
            mc_level=mc_level,
            num_chunks=num_chunks,
            eta=eta,
            enable_pbar=enable_pbar,
            output_type="trimesh"
        )[0]

        # Convert to trimesh format with enhanced colors
        trimesh_mesh = trimesh.Trimesh(
            vertices=mesh.vertices,
            faces=mesh.faces,
            process=False
        )

        # Apply dimension scaling
        if maintain_aspect_ratio:
            # Scale uniformly based on the largest dimension
            current_bounds = trimesh_mesh.bounds
            current_size = current_bounds[1] - current_bounds[0]
            target_size = max(target_width, target_height, target_depth)
            current_max = max(current_size)
            scale_factor = target_size / current_max if current_max > 0 else 1.0
            trimesh_mesh.apply_scale([scale_factor, scale_factor, scale_factor])
        else:
            # Apply individual axis scaling
            current_bounds = trimesh_mesh.bounds
            current_size = current_bounds[1] - current_bounds[0]

            # Calculate scale factors for each axis
            scale_factors = [1.0, 1.0, 1.0]
            if current_size[0] > 0:
                scale_factors[0] = (target_width / current_size[0]) * scale_x
            if current_size[1] > 0:
                scale_factors[1] = (target_height / current_size[1]) * scale_y
            if current_size[2] > 0:
                scale_factors[2] = (target_depth / current_size[2]) * scale_z

            trimesh_mesh.apply_scale(scale_factors)

        # Add better colors and materials if vertices exist
        if hasattr(mesh, 'colors') and mesh.colors is not None:
            trimesh_mesh.visual.vertex_colors = mesh.colors
        else:
            # Generate procedural colors based on vertex positions for better visualization
            vertices_normalized = (trimesh_mesh.vertices - trimesh_mesh.vertices.min(axis=0)) / (
                trimesh_mesh.vertices.max(axis=0) - trimesh_mesh.vertices.min(axis=0) + 1e-8
            )
            # Create rainbow-like coloring based on height (Y-axis)
            colors = np.zeros((len(trimesh_mesh.vertices), 4))
            colors[:, 0] = vertices_normalized[:, 1]  # Red based on height
            colors[:, 1] = 0.6 + 0.4 * vertices_normalized[:, 0]  # Green based on X
            colors[:, 2] = 0.8 + 0.2 * vertices_normalized[:, 2]  # Blue based on Z
            colors[:, 3] = 1.0  # Full alpha
            colors = (colors * 255).astype(np.uint8)
            trimesh_mesh.visual.vertex_colors = colors

        # Create temporary file for GLB output
        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as tmp_file:
            output_path = tmp_file.name

        # Export as GLB with better settings
        trimesh_mesh.export(output_path, file_type='glb')

        # Get final dimensions for status
        final_bounds = trimesh_mesh.bounds
        final_size = final_bounds[1] - final_bounds[0]

        status_msg = f"✅ 3D mesh generated successfully! (Steps: {num_inference_steps}, Guidance: {guidance_scale})\n📏 Final size: {final_size[0]:.2f} × {final_size[1]:.2f} × {final_size[2]:.2f} units"

        return output_path, status_msg

    except Exception as e:
        error_msg = f"❌ Error generating 3D mesh: {str(e)}"
        return None, error_msg

def reset_parameters():
    """Reset all parameters to default values"""
    return 24, 5.0, 1.01, 384, 0.0, 8000, 0.0, True, 1.0, 1.0, 1.0, True, 10.0, 10.0, 10.0

def clear_outputs():
    """Clear all outputs"""
    return None, None, ""

# Create Gradio interface
with gr.Blocks(
    title="🎨 Advanced Image to 3D Generator",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 1600px !important;
        margin: 0 auto;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .parameter-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .status-box {
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .model-viewer {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    .input-section {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 6px 25px rgba(0,0,0,0.1);
    }
    .preset-buttons {
        display: flex;
        gap: 0.5rem;
        margin: 0.8rem 0;
        flex-wrap: wrap;
    }
    .parameter-group {
        background: rgba(255,255,255,0.3);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255,255,255,0.2);
    }
    """
) as demo:

    # Header
    gr.HTML("""
    <div class="main-header">
        <h1>🎨 Advanced Image to 3D Generator</h1>
        <p>Upload an image and generate a 3D GLB model with customizable parameters using Hunyuan3D</p>
    </div>
    """)

    with gr.Row():
        # Left column - Input and Parameters (30% width)
        with gr.Column(scale=3, elem_classes="input-section"):
            gr.HTML("<h3 style='text-align: center; color: #333; margin-bottom: 1rem;'>📤 Upload Image</h3>")

            image_input = gr.Image(
                label="Drag and drop your image here",
                type="filepath",
                height=280,
                elem_id="image_upload"
            )

            # Generation Parameters Section
            gr.HTML("<h3 style='text-align: center; color: #333; margin: 1.5rem 0 1rem 0;'>⚙️ Generation Parameters</h3>")

            # Quality Presets
            gr.HTML("<h4 style='color: #555; margin-bottom: 0.5rem;'>🎯 Quality Presets</h4>")
            with gr.Row():
                fast_preset = gr.Button("⚡ Fast", size="sm", variant="secondary")
                balanced_preset = gr.Button("⚖️ Balanced", size="sm", variant="primary")
                quality_preset = gr.Button("💎 High Quality", size="sm", variant="secondary")
                custom_preset = gr.Button("🔧 Custom", size="sm", variant="secondary")

            # Core Parameters
            with gr.Group(elem_classes="parameter-group"):
                gr.HTML("<h4 style='color: #444; margin-bottom: 0.8rem;'>🔧 Core Settings</h4>")

                num_inference_steps = gr.Slider(
                    minimum=1, maximum=50, value=24, step=1,
                    label="Inference Steps",
                    info="Higher = better quality, slower generation"
                )

                guidance_scale = gr.Slider(
                    minimum=1.0, maximum=20.0, value=5.0, step=0.5,
                    label="Guidance Scale",
                    info="Higher = follows image more closely"
                )

                eta = gr.Slider(
                    minimum=0.0, maximum=1.0, value=0.0, step=0.1,
                    label="ETA (Noise Schedule)",
                    info="Controls randomness in generation"
                )

            # Advanced Parameters
            with gr.Accordion("🔬 Advanced Settings", open=False):
                with gr.Group(elem_classes="parameter-group"):
                    gr.HTML("<h4 style='color: #444; margin-bottom: 0.8rem;'>📐 Geometry Settings</h4>")

                    box_v = gr.Slider(
                        minimum=0.5, maximum=2.0, value=1.01, step=0.01,
                        label="Box Volume",
                        info="3D bounding box size"
                    )

                    octree_resolution = gr.Slider(
                        minimum=128, maximum=512, value=384, step=32,
                        label="Octree Resolution",
                        info="Higher = more detailed geometry"
                    )

                    mc_level = gr.Slider(
                        minimum=-1.0, maximum=1.0, value=0.0, step=0.1,
                        label="Marching Cubes Level",
                        info="Surface extraction threshold"
                    )

                    num_chunks = gr.Slider(
                        minimum=1000, maximum=16000, value=8000, step=1000,
                        label="Number of Chunks",
                        info="Processing chunk size (affects memory usage)"
                    )

                with gr.Group(elem_classes="parameter-group"):
                    gr.HTML("<h4 style='color: #444; margin-bottom: 0.8rem;'>📏 Dimension Control</h4>")

                    maintain_aspect_ratio = gr.Checkbox(
                        value=True,
                        label="Maintain Aspect Ratio",
                        info="Keep original proportions when scaling"
                    )

                    with gr.Row():
                        target_width = gr.Number(
                            value=10.0,
                            label="Target Width",
                            info="Desired width in units"
                        )
                        target_height = gr.Number(
                            value=10.0,
                            label="Target Height",
                            info="Desired height in units"
                        )
                        target_depth = gr.Number(
                            value=10.0,
                            label="Target Depth",
                            info="Desired depth in units"
                        )

                    with gr.Row():
                        scale_x = gr.Slider(
                            minimum=0.1, maximum=5.0, value=1.0, step=0.1,
                            label="X-Scale Multiplier",
                            info="Additional X-axis scaling"
                        )
                        scale_y = gr.Slider(
                            minimum=0.1, maximum=5.0, value=1.0, step=0.1,
                            label="Y-Scale Multiplier",
                            info="Additional Y-axis scaling"
                        )
                        scale_z = gr.Slider(
                            minimum=0.1, maximum=5.0, value=1.0, step=0.1,
                            label="Z-Scale Multiplier",
                            info="Additional Z-axis scaling"
                        )

                with gr.Group(elem_classes="parameter-group"):
                    gr.HTML("<h4 style='color: #444; margin-bottom: 0.8rem;'>🖥️ Interface Settings</h4>")

                    enable_pbar = gr.Checkbox(
                        value=True,
                        label="Show Progress Bar",
                        info="Display generation progress"
                    )

            # Control Buttons
            with gr.Row():
                generate_btn = gr.Button(
                    "🚀 Generate 3D Model",
                    variant="primary",
                    size="lg"
                )
                reset_btn = gr.Button(
                    "🔄 Reset Parameters",
                    variant="secondary"
                )
                clear_btn = gr.Button(
                    "🗑️ Clear All",
                    variant="secondary"
                )

        # Right column - Output (70% width)
        with gr.Column(scale=7, elem_classes="model-viewer"):
            gr.HTML("<h3 style='text-align: center; color: white; margin-bottom: 1.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>📦 Generated 3D Model</h3>")

            # Status display
            status_display = gr.Textbox(
                label="Status",
                value="Ready to generate... Upload an image and adjust parameters.",
                interactive=False,
                elem_classes="status-box"
            )

            # 3D Model viewer - Much larger now
            model_output = gr.Model3D(
                label="Interactive 3D GLB Model",
                height=650,
                camera_position=(2, 2, 2),
                zoom_speed=0.5,
                pan_speed=0.5
            )

            # Lower section with download and summary
            with gr.Row():
                # Download section
                with gr.Column(scale=1):
                    gr.HTML("<h4 style='color: white; margin-bottom: 0.5rem;'>💾 Download</h4>")
                    download_file = gr.File(
                        label="Download GLB file",
                        interactive=False
                    )

                # Parameter Summary
                with gr.Column(scale=1):
                    gr.HTML("<h4 style='color: white; margin-bottom: 0.5rem;'>📊 Current Settings</h4>")
                    param_summary = gr.HTML(
                        """
                        <div style="font-family: 'Courier New', monospace; font-size: 13px; background: rgba(255,255,255,0.15);
                                    padding: 12px; border-radius: 8px; color: white; backdrop-filter: blur(10px);
                                    border: 1px solid rgba(255,255,255,0.2);">
                            <strong style="color: #ffd700;">Current Parameters:</strong><br>
                            <span style="color: #87ceeb;">Steps:</span> 24 | <span style="color: #87ceeb;">Guidance:</span> 5.0 | <span style="color: #87ceeb;">ETA:</span> 0.0<br>
                            <span style="color: #98fb98;">Box Volume:</span> 1.01 | <span style="color: #98fb98;">Resolution:</span> 384<br>
                            <span style="color: #ffa07a;">MC Level:</span> 0.0 | <span style="color: #ffa07a;">Chunks:</span> 8000<br>
                            <span style="color: #dda0dd;">Dimensions:</span> 10.0×10.0×10.0 | <span style="color: #dda0dd;">Aspect Ratio:</span> Yes<br>
                            <span style="color: #f0e68c;">Scale XYZ:</span> 1.0×1.0×1.0
                        </div>
                        """
                    )

    # Instructions


    # Preset functions
    def set_fast_preset():
        return 12, 3.0, 0.0, 1.0, 256, 0.0, 6000, True, 1.0, 1.0, 1.0, True, 10.0, 10.0, 10.0

    def set_balanced_preset():
        return 24, 5.0, 0.0, 1.01, 384, 0.0, 8000, True, 1.0, 1.0, 1.0, True, 10.0, 10.0, 10.0

    def set_quality_preset():
        return 40, 8.0, 0.1, 1.02, 512, 0.0, 10000, True, 1.0, 1.0, 1.0, True, 10.0, 10.0, 10.0

    def set_custom_preset():
        return 24, 5.0, 0.0, 1.01, 384, 0.0, 8000, True, 1.0, 1.0, 1.0, True, 10.0, 10.0, 10.0

    # Update parameter summary
    def update_param_summary(steps, guidance, eta, box_v, resolution, mc_level, chunks, scale_x, scale_y, scale_z, maintain_ratio, width, height, depth):
        ratio_text = "Yes" if maintain_ratio else "No"
        return f"""
        <div style="font-family: 'Courier New', monospace; font-size: 13px; background: rgba(255,255,255,0.15);
                    padding: 12px; border-radius: 8px; color: white; backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);">
            <strong style="color: #ffd700;">Current Parameters:</strong><br>
            <span style="color: #87ceeb;">Steps:</span> {steps} | <span style="color: #87ceeb;">Guidance:</span> {guidance} | <span style="color: #87ceeb;">ETA:</span> {eta}<br>
            <span style="color: #98fb98;">Box Volume:</span> {box_v} | <span style="color: #98fb98;">Resolution:</span> {resolution}<br>
            <span style="color: #ffa07a;">MC Level:</span> {mc_level} | <span style="color: #ffa07a;">Chunks:</span> {chunks}<br>
            <span style="color: #dda0dd;">Dimensions:</span> {width}×{height}×{depth} | <span style="color: #dda0dd;">Aspect Ratio:</span> {ratio_text}<br>
            <span style="color: #f0e68c;">Scale XYZ:</span> {scale_x}×{scale_y}×{scale_z}
        </div>
        """

    # Event handlers
    def update_status_and_generate(image, steps, guidance, box_v, resolution, mc_level, chunks, eta, pbar,
                                  scale_x, scale_y, scale_z, maintain_ratio, width, height, depth):
        if image is None:
            return None, None, "Please upload an image first."

        # Update status immediately
        yield None, None, f"🔄 Starting 3D generation with {steps} steps..."

        # Generate the mesh
        glb_path, status = generate_3d_mesh(
            image, steps, guidance, box_v, resolution, mc_level, chunks, eta, pbar,
            scale_x, scale_y, scale_z, maintain_ratio, width, height, depth
        )

        if glb_path:
            yield glb_path, glb_path, status
        else:
            yield None, None, status

    # Button events
    generate_btn.click(
        fn=update_status_and_generate,
        inputs=[image_input, num_inference_steps, guidance_scale, box_v,
                octree_resolution, mc_level, num_chunks, eta, enable_pbar,
                scale_x, scale_y, scale_z, maintain_aspect_ratio,
                target_width, target_height, target_depth],
        outputs=[model_output, download_file, status_display],
        show_progress=True
    )

    # Preset button events
    fast_preset.click(
        fn=set_fast_preset,
        outputs=[num_inference_steps, guidance_scale, eta, box_v,
                octree_resolution, mc_level, num_chunks, enable_pbar,
                scale_x, scale_y, scale_z, maintain_aspect_ratio,
                target_width, target_height, target_depth]
    )

    balanced_preset.click(
        fn=set_balanced_preset,
        outputs=[num_inference_steps, guidance_scale, eta, box_v,
                octree_resolution, mc_level, num_chunks, enable_pbar,
                scale_x, scale_y, scale_z, maintain_aspect_ratio,
                target_width, target_height, target_depth]
    )

    quality_preset.click(
        fn=set_quality_preset,
        outputs=[num_inference_steps, guidance_scale, eta, box_v,
                octree_resolution, mc_level, num_chunks, enable_pbar,
                scale_x, scale_y, scale_z, maintain_aspect_ratio,
                target_width, target_height, target_depth]
    )

    custom_preset.click(
        fn=set_custom_preset,
        outputs=[num_inference_steps, guidance_scale, eta, box_v,
                octree_resolution, mc_level, num_chunks, enable_pbar,
                scale_x, scale_y, scale_z, maintain_aspect_ratio,
                target_width, target_height, target_depth]
    )

    reset_btn.click(
        fn=reset_parameters,
        outputs=[num_inference_steps, guidance_scale, box_v,
                octree_resolution, mc_level, num_chunks, eta, enable_pbar,
                scale_x, scale_y, scale_z, maintain_aspect_ratio,
                target_width, target_height, target_depth]
    )

    clear_btn.click(
        fn=clear_outputs,
        outputs=[image_input, model_output, download_file, status_display]
    )

    # Update parameter summary when sliders change
    dimension_inputs = [num_inference_steps, guidance_scale, eta, box_v, octree_resolution, mc_level, num_chunks,
                       scale_x, scale_y, scale_z, maintain_aspect_ratio, target_width, target_height, target_depth]



    # Auto-update status when image is uploaded
    image_input.change(
        fn=lambda img: "Image uploaded! Adjust parameters and click 'Generate 3D Model'." if img else "Ready to generate... Upload an image and adjust parameters.",
        inputs=[image_input],
        outputs=[status_display]
    )

# Launch the interface
if __name__ == "__main__":
    # For Colab, use share=True to get a public link
    demo.launch(
        share=True,  # Creates a public shareable link
        debug=True,
        height=1000,
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860
    )