document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const errorMessage = document.getElementById("error-message");

    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        // Hide previous error messages
        errorMessage.style.display = "none";

        // Show loading state
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector(".btn-text");
        const btnLoader = submitBtn.querySelector(".btn-loader");

        btnText.style.display = "none";
        btnLoader.style.display = "block";
        submitBtn.disabled = true;

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // Store user data in localStorage
                localStorage.setItem("user", JSON.stringify(data.user));

                // Show success state briefly
                btnText.textContent = "Success!";
                btnText.style.display = "block";
                btnLoader.style.display = "none";

                // Redirect to dashboard after brief delay
                setTimeout(() => {
                    window.location.href = "/dashboard";
                }, 500);
            } else {
                // Show error message
                errorMessage.textContent = data.detail || "Login failed";
                errorMessage.style.display = "block";

                // Shake animation for error
                loginForm.style.animation = "shake 0.5s ease-in-out";
                setTimeout(() => {
                    loginForm.style.animation = "";
                }, 500);
            }
        } catch (error) {
            console.error("Login error:", error);
            errorMessage.textContent = "Connection error. Please try again.";
            errorMessage.style.display = "block";

            // Shake animation for error
            loginForm.style.animation = "shake 0.5s ease-in-out";
            setTimeout(() => {
                loginForm.style.animation = "";
            }, 500);
        } finally {
            // Reset button state
            setTimeout(() => {
                btnText.textContent = "Sign In";
                btnText.style.display = "block";
                btnLoader.style.display = "none";
                submitBtn.disabled = false;
            }, 1000);
        }
    });

    // Add shake animation CSS
    const style = document.createElement("style");
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
    `;
    document.head.appendChild(style);
});

// Fill credentials function for demo accounts
function fillCredentials(username, password) {
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");

    // Clear any existing values
    usernameInput.value = "";
    passwordInput.value = "";

    // Add typing animation effect
    typeText(usernameInput, username, () => {
        typeText(passwordInput, password);
    });

    // Add visual feedback
    const inputs = document.querySelectorAll("#username, #password");
    inputs.forEach((input) => {
        input.style.borderColor = "#667eea";
        input.style.boxShadow = "0 0 0 3px rgba(102, 126, 234, 0.1)";
        setTimeout(() => {
            input.style.borderColor = "";
            input.style.boxShadow = "";
        }, 2000);
    });
}

// Typing animation function
function typeText(element, text, callback) {
    let index = 0;
    element.focus();

    const typeInterval = setInterval(() => {
        element.value += text[index];
        index++;

        if (index >= text.length) {
            clearInterval(typeInterval);
            if (callback) {
                setTimeout(callback, 200);
            }
        }
    }, 50);
}

// Add keyboard shortcuts
document.addEventListener("keydown", function (e) {
    // Alt + 1-4 for quick demo account selection
    if (e.altKey && e.key >= "1" && e.key <= "4") {
        e.preventDefault();
        const accounts = [
            ["admin", "admin123"],
            ["manager_cl1", "manager123"],
            ["emoc_cl1", "emoc123"],
            ["counselor_cl1", "outdoor123"],
        ];

        const accountIndex = parseInt(e.key) - 1;
        if (accounts[accountIndex]) {
            fillCredentials(
                accounts[accountIndex][0],
                accounts[accountIndex][1]
            );
        }
    }
});

// Add focus management
document.addEventListener("DOMContentLoaded", function () {
    // Focus on username field when page loads
    setTimeout(() => {
        document.getElementById("username").focus();
    }, 100);

    // Enter key navigation
    document
        .getElementById("username")
        .addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                document.getElementById("password").focus();
            }
        });
});

// Add demo account hover effects
document.addEventListener("DOMContentLoaded", function () {
    const demoItems = document.querySelectorAll(".demo-item");

    demoItems.forEach((item) => {
        item.addEventListener("mouseenter", function () {
            this.style.transform = "translateY(-2px) scale(1.02)";
        });

        item.addEventListener("mouseleave", function () {
            this.style.transform = "";
        });
    });
});
