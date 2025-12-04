import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os

# Ensure output directory exists
OUTPUT_DIR = "journal_figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set style
plt.style.use('dark_background')
colors = {'accent': '#a855f7', 'secondary': '#3b82f6', 'bg': '#171717', 'text': '#ffffff'}

def generate_ema_smoothing():
    """Figure 1: Visualizing the impact of EMA smoothing on jittery hand data."""
    t = np.linspace(0, 10, 100)
    # True path (smooth curve)
    true_path = np.sin(t) * 100 + 200
    
    # Jittery input (simulating raw MediaPipe output)
    noise = np.random.normal(0, 15, 100)
    raw_input = true_path + noise
    
    # EMA Smoothing
    alpha = 0.2
    smoothed = [raw_input[0]]
    for i in range(1, len(raw_input)):
        smoothed.append(alpha * raw_input[i] + (1 - alpha) * smoothed[-1])
    
    plt.figure(figsize=(10, 5), facecolor=colors['bg'])
    ax = plt.gca()
    ax.set_facecolor(colors['bg'])
    
    plt.plot(t, raw_input, color='gray', alpha=0.5, label='Raw Input (Jittery)', linewidth=1)
    plt.plot(t, true_path, color=colors['secondary'], linestyle='--', alpha=0.5, label='True Path', linewidth=1)
    plt.plot(t, smoothed, color=colors['accent'], linewidth=3, label='EMA Smoothed')
    
    plt.title("Impact of Exponential Moving Average (EMA) on Hand Tracking", color=colors['text'], fontsize=14, pad=20)
    plt.xlabel("Time (frames)", color=colors['text'])
    plt.ylabel("Pixel Coordinate (X)", color=colors['text'])
    plt.legend(facecolor=colors['bg'], edgecolor='white', labelcolor='white')
    plt.grid(color='gray', alpha=0.2)
    plt.tick_params(colors='white')
    
    # Annotation
    plt.annotate('Micro-jitter removed', xy=(5, 100), xytext=(6, 50),
                 arrowprops=dict(facecolor='white', shrink=0.05), color='white')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/ema_smoothing.png", dpi=300)
    plt.close()
    print("Generated ema_smoothing.png")

def generate_latency_comparison():
    """Figure 2: Latency comparison between SDXL and SDXL-Turbo."""
    models = ['Standard SDXL', 'SDXL-Turbo (Ours)']
    times = [15.0, 0.8] # Seconds
    
    plt.figure(figsize=(8, 6), facecolor=colors['bg'])
    ax = plt.gca()
    ax.set_facecolor(colors['bg'])
    
    bars = plt.bar(models, times, color=[colors['secondary'], colors['accent']], width=0.5)
    
    plt.title("Inference Latency: The Real-Time Breakthrough", color=colors['text'], fontsize=14, pad=20)
    plt.ylabel("Generation Time (seconds)", color=colors['text'])
    plt.grid(axis='y', color='gray', alpha=0.2)
    plt.tick_params(colors='white')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                 f'{height}s',
                 ha='center', va='bottom', color='white', fontsize=12, fontweight='bold')

    # Add text annotation
    plt.text(0.5, 10, "18x Faster", ha='center', color=colors['accent'], fontsize=20, fontweight='bold', rotation=0)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/latency_comparison.png", dpi=300)
    plt.close()
    print("Generated latency_comparison.png")

def generate_architecture_diagram():
    """Figure 3: 3-Thread Architecture Diagram."""
    fig, ax = plt.subplots(figsize=(12, 6), facecolor=colors['bg'])
    ax.set_facecolor(colors['bg'])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')

    def draw_box(x, y, w, h, color, label, sublabel=""):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", 
                                      linewidth=2, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + 0.3, label, ha='center', va='center', color=color, fontsize=12, fontweight='bold')
        ax.text(x + w/2, y + h/2 - 0.3, sublabel, ha='center', va='center', color='white', fontsize=9)

    # Thread 1: CV
    draw_box(1, 2, 2.5, 2, colors['secondary'], "CV Thread", "Webcam + MediaPipe\n(30 FPS)")
    
    # Thread 2: Main
    draw_box(4.5, 2, 3, 2, 'white', "Main Thread", "UI Event Loop\nState Management")
    
    # Thread 3: GenAI
    draw_box(8.5, 2, 2.5, 2, colors['accent'], "GenAI Thread", "Stable Diffusion\n(Async Queue)")

    # Arrows
    style = "Simple, tail_width=0.5, head_width=4, head_length=8"
    kw = dict(arrowstyle=style, color="gray")
    
    # CV -> Main
    a1 = patches.FancyArrowPatch((3.6, 3), (4.4, 3), **kw)
    ax.add_patch(a1)
    ax.text(4, 3.2, "Landmarks", ha='center', color='gray', fontsize=8)

    # Main -> GenAI
    a2 = patches.FancyArrowPatch((7.6, 3.5), (8.4, 3.5), **kw)
    ax.add_patch(a2)
    ax.text(8, 3.7, "Request", ha='center', color='gray', fontsize=8)

    # GenAI -> Main
    a3 = patches.FancyArrowPatch((8.4, 2.5), (7.6, 2.5), **kw)
    ax.add_patch(a3)
    ax.text(8, 2.3, "Image", ha='center', color='gray', fontsize=8)

    # Shared Resource (Lock)
    rect_lock = patches.Rectangle((5, 0.5), 2, 1, linewidth=1, edgecolor='red', facecolor='none', linestyle='--')
    ax.add_patch(rect_lock)
    ax.text(6, 1, "Shared Canvas\n(Locked)", ha='center', va='center', color='red', fontsize=9)
    
    # Lines to lock
    ax.plot([5.5, 5.5], [1.5, 2], color='red', linestyle=':', alpha=0.5) # From Main

    plt.title("3-Thread Architecture & Data Flow", color='white', fontsize=16)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/architecture_diagram.png", dpi=300)
    plt.close()
    print("Generated architecture_diagram.png")

if __name__ == "__main__":
    generate_ema_smoothing()
    generate_latency_comparison()
    generate_architecture_diagram()
