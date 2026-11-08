from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

out = Path("results/figures")
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
fig = plt.figure(figsize=(13.4, 4.25), facecolor="#f4f7fb")
fig.text(.038,.895,"Causal assumptions for treatment assignment",size=23,color="#152b42",weight="bold")
fig.text(.04,.815,"The NSW experiment and the separate overlap simulations",size=11,color="#40556b")

titles = ("A  NSW experiment", "B  Observed selection", "C  Hidden confounding")
subtitles = ("Randomized historical assignment", "Simulation with measured covariates", "Simulation with an unobserved cause")
notes = ("Empty back-door adjustment set", "Adjust for pretreatment W", "Adjusting for W leaves a path open")
for i, (title, subtitle, note) in enumerate(zip(titles, subtitles, notes)):
    ax = fig.add_axes([.038+.318*i,.15,.291,.59])
    ax.set(xlim=(0, 10), ylim=(0, 7))
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((.03,.06),9.94,6.86, boxstyle="round,pad=0.02,rounding_size=0.22",
                                facecolor="white",edgecolor="#d4dee8",linewidth=1.2))
    ax.text(.48,6.30,title,size=13,weight="bold",color="#152b42")
    ax.text(.48,5.71,subtitle,size=9.2,color="#40556b")
    colors = {"W":"#1a6571","T":"#345880","Y":"#345880","U":"#965629"}
    positions = {"W":(2.85,4.65),"T":(2.6,2.95),"Y":(7.4,2.95),"U":(7.15,1.38)}
    def edge(source, target, color="#53718d"):
        ax.add_patch(FancyArrowPatch(positions[source],positions[target],shrinkA=12,shrinkB=13,
                                    arrowstyle="-|>",mutation_scale=12,linewidth=1.6,color=color))
    edge("W","Y")
    edge("T","Y")
    if i > 0:
        edge("W","T")
    if i == 2:
        edge("U","Y","#965629")
        edge("U","T","#965629")
    for label in ("W","T","Y","U") if i==2 else ("W","T","Y"):
        x,y=positions[label]
        ax.text(x,y,label,ha="center",va="center",size=12,weight="bold",color="white",
                bbox={"boxstyle":"round,pad=.49","facecolor":colors[label],"edgecolor":"none"})
    ax.text(.48,.56,note,size=9.3,weight="bold",color="#152b42")
fig.text(.04,.075,"W  Pretreatment covariates    •    T  Training assignment    •    Y  Subsequent earnings    •    U  Simulated hidden cause",
         size=9.6,color="#40556b")
for extension in ("svg","png"):
    fig.savefig(out / f"nsw_causal_dag.{extension}", dpi=230, facecolor=fig.get_facecolor())
plt.close(fig)
