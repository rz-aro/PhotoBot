window.onload = () => {
    lucide.createIcons();
};

document.addEventListener("DOMContentLoaded", () => {
    // Loader fade out
    const loader = document.getElementById("loader");
    const images = document.querySelectorAll("#macy-container img");
    let loadedCount = 0;
    

    function hideLoader() {
        loader.style.opacity = "0";
    }

    if (images.length === 0) hideLoader();
    
    const votesImages = [];
    fetch("/getvotes")
        .then((response) => response.json())
        .then((data) => {
            if (data.votes) {
                votesImages.push(...data.votes);
            }
        });
    

    images.forEach((img) => {
        if (img.complete) {
            loadedCount++;
            if (loadedCount === images.length) hideLoader();
        } else {
            img.addEventListener("load", () => {
                loadedCount++;
                if (loadedCount === images.length) hideLoader();
            });
            img.addEventListener("error", () => {
                loadedCount++;
                if (loadedCount === images.length) hideLoader();
            });
        }
    });

    // Profile card animation
    const pficon = document.querySelector(".pficon");
    const profileCard = document.querySelector(".profile-card");

    pficon?.addEventListener("mouseenter", () => {
        profileCard.classList.remove("hidden");
        setTimeout(() => {
            profileCard.classList.remove("opacity-0", "translate-y-4");
            profileCard.classList.add("opacity-100", "translate-y-0");
        }, 10);
    });

    pficon?.addEventListener("mouseleave", () => {
        profileCard.classList.remove("opacity-100", "translate-y-0");
        profileCard.classList.add("opacity-0", "translate-y-4");
        setTimeout(() => {
            profileCard.classList.add("hidden");
        }, 300);
    });

    // Macy layout
    Macy({
        container: "#macy-container",
        trueOrder: false,
        waitForImages: false,
        margin: 15,
        columns: 5,
        breakAt: {
            1200: { margin: 10, columns: 5 },
            800: { margin: 5, columns: 5 },
            600: { margin: 5, columns: 3 },
        },
    });


    // Image modal
    document.querySelectorAll("img").forEach((img) => {

        img.addEventListener("click", function () {
            if (this.classList.contains("select-image-checkbox")) {
                const checkbox = this.previousElementSibling;
                if (votesImages.length >= 3 && !checkbox.checked) {
                    showNotification("You can only select a maximum of 3 images.");
                    return;
                }
                if (!checkbox.checked) {
                    votesImages.push(this.dataset.id);
                    if (votesImages.length === 3) {
                        showNotification("Your changes have been saved. You can now submit your votes by pressing on the check icon.");
                    }
                } else {
                    votesImages.splice(votesImages.indexOf(this.dataset.id), 1);
                }

                // push changes as a json to /vote
                fetch("/vote", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ votes: votesImages }),
                })
                    .then((response) => response.json())
                    .then((data) => {
                        console.log("Vote updated:", data);
                    })
                    .catch((error) => {
                        console.error("Error updating vote:", error);
                    });
                checkbox.checked = !checkbox.checked;
                return;
            };
            const src = this.getAttribute("src");
            const captionText = (this.getAttribute("data-caption") || "")
                .replace(/:[a-zA-Z0-9_]+:/g, "")
                .replace(/\*/g, "")
                .replace(/"/g, "");
            const user = this.getAttribute("data-user") || "";

            const modal = document.createElement("div");
            modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0); display: flex;
        flex-direction: column; justify-content: center; align-items: center;
        transition: background-color 0.4s cubic-bezier(.25,.8,.25,1); z-index: 99999;
      `;

            const modalImg = document.createElement("img");
            modalImg.src = src;
            modalImg.style.cssText = `
        opacity: 0;
        border-radius: 4px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
        transition: all 0.4s cubic-bezier(.25,.8,.25,1);
        max-width: 90vw;
        max-height: 70vh;
        width: auto;
        height: auto;
        display: block;
        margin: 0 auto;
      `;

            const caption = document.createElement("div");
            caption.innerHTML = `${captionText}<br> - ${user}`;
            caption.style.cssText = `
        color: #eee; 
        font-size: clamp(1rem, 2vw, 1.5rem); 
        text-align: center;
        opacity: 0; 
        margin-top: 20px;
        max-width: 80vw;
        max-height: 20vh;
        overflow: auto;
        transition: opacity 0.4s cubic-bezier(.25,.8,.25,1);
      `;

            modal.appendChild(modalImg);
            modal.appendChild(caption);
            document.body.appendChild(modal);

            setTimeout(() => {
                modal.style.backgroundColor = "rgba(0, 0, 0, 0.8)";
                modalImg.style.opacity = "1";
                caption.style.opacity = "1";
            }, 10);

            modal.addEventListener("click", () => {
                modal.style.backgroundColor = "rgba(0, 0, 0, 0)";
                modalImg.style.opacity = "0";
                caption.style.opacity = "0";
                setTimeout(() => {
                    document.body.removeChild(modal);
                }, 400);
            });
        });
    });
    var viewBool = false;

    // vote logic
    const votebtn = document.getElementById("vote-button");
    const voteIcon = document.getElementById("vote-icon");
    const checkIcon = document.getElementById("check-icon");
    const allImages = document.querySelectorAll("#macy-container img");



    if (votebtn) {
        votebtn.addEventListener("click", () => {
            viewBool = true;
            if (votebtn.dataset.currentState === "vote") {
                showNotification("Cast your votes! You can select a maximum of 3 pics.");
                voteIcon.classList.add("move");
                checkIcon.classList.add("move");
                votebtn.dataset.currentState = "check";
                allImages.forEach((img) => {
                    img.classList.toggle("select-image-checkbox");
                    img.classList.toggle("hovernow");
                });
            } else {
                voteIcon.classList.remove("move");
                checkIcon.classList.remove("move");
                votebtn.dataset.currentState = "vote";
                allImages.forEach((img) => {
                    img.classList.toggle("select-image-checkbox");
                    img.classList.toggle("hovernow");
                });
                showNotification("Your votes have been casted successfully!");
            }

        });
    }
    function showNotification(message, duration = 3000) {
        console.log("Notification:", message);
        const bar = document.createElement('div');
        bar.className = 'flex items-center gap-3 bg-gray-800 text-gray-200 px-4 py-2 rounded-md shadow-md animate- opacity-0 pointer-events-none transition-all duration-300 ease-in-out';
        bar.innerHTML = `
            <div class="bg-blue-700 p-2 rounded-md">
                <i data-lucide="bell" class="w-4 h-4 text-white"></i>
            </div>
            <span class="text-sm" id="notification-message">${message}</span>`;
        const closenotif = document.createElement('button');
        closenotif.className = 'ml-auto text-gray-400 hover:text-gray-200';
        closenotif.innerHTML = `<i data-lucide="x" class="w-4 h-4"></i>`;
        bar.appendChild(closenotif);
        const container = document.getElementById('notification-container');
        container.appendChild(bar);

        // Re-render lucide icons in the newly added notification bar
        lucide.createIcons();

        bar.classList.remove('opacity-0', 'pointer-events-none');
        bar.classList.add('opacity-100');
        setTimeout(() => {
            bar.classList.remove('opacity-100');
            bar.classList.add('opacity-0', 'pointer-events-none');
            setTimeout(() => {
                bar.remove();
            }, 300);

        }, duration);

        closenotif.addEventListener('click', () => {
            bar.classList.remove('opacity-100');
            bar.classList.add('opacity-0', 'pointer-events-none');
            setTimeout(() => {
                bar.remove();
            }, 300);
        });
    }

    // set top of tooltip
    const tooltip = document.querySelector(".overlay-fortooltip");
    const voteicon = document.getElementById("vote-icon");
    tooltip.style.top = voteicon.getBoundingClientRect().top + "px";

    const tooltipText = document.querySelector(".tooltip-text");
    setTimeout(() => {
        setTimeout(() => {
            tooltipText.style.transform = "translate(0,0)";
        }, 1000);
        
        setTimeout(() => {
            tooltipText.style.transform = "translate(-200%, 0)";
        }, 5000);
    }, 100)
    setInterval(() => {
        if (!viewBool) {
            viewBool = false;
            setTimeout(() => {
                tooltipText.style.transform = "translate(0,0)";
            }, 1000);
            setTimeout(() => {
                tooltipText.style.transform = "translate(-200%, 0)";
            }, 5000);
        }
    }, 8000);

    document.addEventListener("screenchange", () => {
        tooltip.style.top = voteicon.getBoundingClientRect().top + "px";
    });

    document.getElementById("reload-button").addEventListener("click", () => {
          // spin the reload icon-button
          console.log('Reloading...');
          const reloadButton = document.getElementById('reload-icon');
          reloadButton.classList.add('animate-spin');
          setTimeout(() => {
            reloadButton.classList.remove('animate-spin');
          }, 1000);
          location.reload();
        });
    
        window.addEventListener("beforeunload", () => {
            const loader = document.getElementById("loader");
            if (loader) {
                loader.style.opacity = "1";
            }
        });
});
