document.addEventListener("DOMContentLoaded", function () {
    console.log("Dashboard loaded"); // Debug log

    // Initialize dashboard
    initializeDashboard();

    // Set up navigation
    setupNavigation();

    // Set up logout
    setupLogout();

    // Set up search functionality
    setupSearch();

    // Load dashboard data
    loadDashboardData();
});

function initializeDashboard() {
    // Get user data from session (passed from template)
    // Note: In a real app, you might get this from an API call

    // Show/hide sections based on user role
    setupRoleBasedAccess();
}

function setupRoleBasedAccess() {
    // This will be handled by the template's {% if user.role == 'admin' %} logic
    // But we can add additional JavaScript-based role management here if needed

    // Example: Hide/show elements based on data attributes
    const userRole = document
        .querySelector("#user-info")
        ?.textContent?.toLowerCase();

    if (userRole && userRole.includes("admin")) {
        console.log("Admin user detected");
        // Additional admin-specific functionality can go here
    }
}

function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const contentSections = document.querySelectorAll(".content-section");

    console.log("Found nav items:", navItems.length); // Debug log
    console.log("Found content sections:", contentSections.length); // Debug log

    navItems.forEach((item) => {
        item.addEventListener("click", function () {
            const targetSection = this.getAttribute("data-section");
            console.log("Clicked section:", targetSection); // Debug log

            // Remove active class from all nav items and sections
            navItems.forEach((nav) => nav.classList.remove("active"));
            contentSections.forEach((section) =>
                section.classList.remove("active")
            );

            // Add active class to clicked nav item
            this.classList.add("active");

            // Show target section
            const targetElement = document.getElementById(
                targetSection + "-section"
            );
            if (targetElement) {
                targetElement.classList.add("active");
                console.log("Activated section:", targetSection); // Debug log
            } else {
                console.error("Section not found:", targetSection + "-section"); // Debug log
            }
        });
    });

    // Make sure overview section is active by default
    const overviewSection = document.getElementById("overview-section");
    const overviewNav = document.querySelector('[data-section="overview"]');
    if (overviewSection && overviewNav) {
        overviewSection.classList.add("active");
        overviewNav.classList.add("active");
    }
}

function setupLogout() {
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        // Remove the inline onclick and use proper event listener
        logoutBtn.removeAttribute("onclick");
        logoutBtn.addEventListener("click", function (e) {
            e.preventDefault();
            if (confirm("Are you sure you want to logout?")) {
                window.location.href = "/logout";
            }
        });
    }
}

function setupSearch() {
    const searchInput = document.getElementById("patient-search");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll("#patients-table-body tr");

            rows.forEach((row) => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? "" : "none";
            });
        });
    }
}

function loadDashboardData() {
    // Load all table data
    loadPatientsData();
    loadEmocData();
    loadBillingData();
    loadUsersData();
    loadClinicsData();
    loadRecentActivity();
}

function loadRecentActivity() {
    const activities = [
        { time: "10:30 AM", desc: "New patient registered: Sarah Ahmed" },
        { time: "09:15 AM", desc: "EMOC case admitted: Emergency delivery" },
        { time: "08:45 AM", desc: "Payment received: ৳2,500" },
        { time: "08:30 AM", desc: "User login: manager_cl1" },
        { time: "08:00 AM", desc: "System backup completed" },
    ];

    const activityList = document.getElementById("activity-list");
    if (activityList) {
        activityList.innerHTML = activities
            .map(
                (activity) => `
            <div class="activity-item">
                <span class="activity-time">${activity.time}</span>
                <span class="activity-desc">${activity.desc}</span>
            </div>
        `
            )
            .join("");
    }
}

function loadPatientsData() {
    const patients = [
        {
            id: "P001",
            name: "Sarah Ahmed",
            age: 28,
            phone: "01712345678",
            lastVisit: "2024-05-30",
        },
        {
            id: "P002",
            name: "Fatima Khan",
            age: 32,
            phone: "01798765432",
            lastVisit: "2024-05-29",
        },
        {
            id: "P003",
            name: "Rashida Begum",
            age: 25,
            phone: "01687654321",
            lastVisit: "2024-05-28",
        },
    ];

    const tbody = document.getElementById("patients-table-body");
    if (tbody) {
        tbody.innerHTML = patients
            .map(
                (patient) => `
            <tr>
                <td>${patient.id}</td>
                <td>${patient.name}</td>
                <td>${patient.age}</td>
                <td>${patient.phone}</td>
                <td>${patient.lastVisit}</td>
                <td>
                    <button class="btn-small">View</button>
                    <button class="btn-small">Edit</button>
                </td>
            </tr>
        `
            )
            .join("");
    }
}

function loadEmocData() {
    const emocCases = [
        {
            id: "EMOC001",
            patient: "Fatima Khan",
            type: "Normal Delivery",
            status: "Active",
            admission: "2024-05-31 08:30",
        },
        {
            id: "EMOC002",
            patient: "Rashida Begum",
            type: "C-Section",
            status: "Completed",
            admission: "2024-05-30 14:15",
        },
        {
            id: "EMOC003",
            patient: "Amina Khatun",
            type: "Emergency",
            status: "Active",
            admission: "2024-05-31 10:45",
        },
    ];

    const tbody = document.getElementById("emoc-table-body");
    if (tbody) {
        tbody.innerHTML = emocCases
            .map(
                (emocCase) => `
            <tr>
                <td>${emocCase.id}</td>
                <td>${emocCase.patient}</td>
                <td>${emocCase.type}</td>
                <td><span class="status ${emocCase.status.toLowerCase()}">${
                    emocCase.status
                }</span></td>
                <td>${emocCase.admission}</td>
                <td>
                    <button class="btn-small">View</button>
                    <button class="btn-small">Update</button>
                </td>
            </tr>
        `
            )
            .join("");
    }
}

function loadBillingData() {
    const bills = [
        {
            id: "B001",
            patient: "Sarah Ahmed",
            service: "Consultation",
            amount: "৳500",
            status: "Paid",
            date: "2024-05-31",
        },
        {
            id: "B002",
            patient: "Fatima Khan",
            service: "Delivery",
            amount: "৳15,000",
            status: "Paid",
            date: "2024-05-30",
        },
        {
            id: "B003",
            patient: "Rashida Begum",
            service: "Ultrasound",
            amount: "৳800",
            status: "Pending",
            date: "2024-05-29",
        },
    ];

    const tbody = document.getElementById("billing-table-body");
    if (tbody) {
        tbody.innerHTML = bills
            .map(
                (bill) => `
            <tr>
                <td>${bill.id}</td>
                <td>${bill.patient}</td>
                <td>${bill.service}</td>
                <td>${bill.amount}</td>
                <td><span class="status ${bill.status.toLowerCase()}">${
                    bill.status
                }</span></td>
                <td>${bill.date}</td>
                <td>
                    <button class="btn-small">View</button>
                    <button class="btn-small">Print</button>
                </td>
            </tr>
        `
            )
            .join("");
    }
}

function loadUsersData() {
    const users = [
        {
            username: "admin",
            fullName: "System Administrator",
            role: "Admin",
            clinic: "All Clinics",
            status: "Active",
        },
        {
            username: "manager_cl1",
            fullName: "Nasirabad Manager",
            role: "Manager",
            clinic: "Nasirabad Clinic",
            status: "Active",
        },
        {
            username: "emoc_cl1",
            fullName: "Nasirabad EMOC Staff",
            role: "EMOC Staff",
            clinic: "Nasirabad Clinic",
            status: "Active",
        },
    ];

    const tbody = document.getElementById("users-table-body");
    if (tbody) {
        tbody.innerHTML = users
            .map(
                (user) => `
            <tr>
                <td>${user.username}</td>
                <td>${user.fullName}</td>
                <td>${user.role}</td>
                <td>${user.clinic}</td>
                <td><span class="status ${user.status.toLowerCase()}">${
                    user.status
                }</span></td>
                <td>
                    <button class="btn-small">Edit</button>
                    <button class="btn-small">Disable</button>
                </td>
            </tr>
        `
            )
            .join("");
    }
}

function loadClinicsData() {
    const clinics = [
        {
            name: "Nasirabad Clinic",
            location: "Nasirabad, Chittagong",
            phone: "01711111111",
            patients: 25,
            staff: 5,
        },
        {
            name: "Jalalabad Clinic",
            location: "Jalalabad, Sylhet",
            phone: "01722222222",
            patients: 18,
            staff: 4,
        },
    ];

    const tbody = document.getElementById("clinics-table-body");
    if (tbody) {
        tbody.innerHTML = clinics
            .map(
                (clinic) => `
            <tr>
                <td>${clinic.name}</td>
                <td>${clinic.location}</td>
                <td>${clinic.phone}</td>
                <td>${clinic.patients}</td>
                <td>${clinic.staff}</td>
                <td>
                    <button class="btn-small">View</button>
                    <button class="btn-small">Edit</button>
                </td>
            </tr>
        `
            )
            .join("");
    }
}

// Additional utility functions
function refreshData() {
    console.log("Refreshing dashboard data...");
    loadDashboardData();
}

// Add event listeners for refresh buttons
document.addEventListener("DOMContentLoaded", function () {
    const refreshBtn = document.getElementById("refresh-logs-btn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            console.log("Refreshing login logs...");
            // In a real app, you would fetch fresh data from the server
            loadUsersData(); // For now, just reload the data
        });
    }
});
