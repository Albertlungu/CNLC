import {
    getSession, requireAuth, logout,
    getUserProfile, updateProfile, upgradeToBusinessOwner,
    getFriends, removeFriend as apiRemoveFriend,
    getNotifications, markNotificationRead,
    searchUsers, sendFriendRequest
} from "./api-client.js";
import { initNavbar } from "./components/navbar.js";

// Check authentication
if (!requireAuth()) {
    throw new Error("Not authenticated");
}
initNavbar("profile");

const session = getSession();
const userId = session.userId;
const username = session.username;

// DOM Elements
const profilePicture = document.getElementById("profilePicture");
const profilePictureInput = document.getElementById("profilePictureInput");
const displayUsername = document.getElementById("displayUsername");
const displayEmail = document.getElementById("displayEmail");
const memberSince = document.getElementById("memberSince");
const profileForm = document.getElementById("profileForm");
const cancelBtn = document.getElementById("cancelBtn");
const openInviteModal = document.getElementById("openInviteModal");
const inviteModal = document.getElementById("inviteModal");
const closeModal = document.querySelector(".close");
const inviteForm = document.getElementById("inviteForm");
const friendsList = document.getElementById("friendsList");
const notificationsList = document.getElementById("notificationsList");
const tabBtns = document.querySelectorAll(".tab-btn");

// Store original form values
let originalFormData = {};

// Initialize profile page
async function initProfile() {
    try {
        // Load user profile data
        const userProfile = await getUserProfile(username);
        
        if (userProfile && userProfile.user) {
            const user = userProfile.user;
            
            // Set display info
            displayUsername.textContent = user.username || username;
            displayEmail.textContent = user.email || "N/A";
            
            // Set member since date
            if (user.createdAt) {
                const date = new Date(user.createdAt);
                memberSince.textContent = date.toLocaleDateString('en-US', { 
                    month: 'short', 
                    year: 'numeric' 
                });
            } else {
                memberSince.textContent = "N/A";
            }
            
            // Extract nested profile/location fields
            const firstName = (user.profile && user.profile.firstName) || user.firstName || "";
            const lastName = (user.profile && user.profile.lastName) || user.lastName || "";
            const city = (user.location && user.location.city) || user.city || "";
            const country = (user.location && user.location.country) || user.country || "";
            
            // Populate form
            document.getElementById("firstName").value = firstName;
            document.getElementById("lastName").value = lastName;
            document.getElementById("email").value = user.email || "";
            document.getElementById("phone").value = user.phone || "";
            document.getElementById("address").value = user.address || "";
            document.getElementById("city").value = city;
            document.getElementById("province").value = user.province || "";
            document.getElementById("postalCode").value = user.postalCode || "";
            document.getElementById("country").value = country;
            
            // Store original data
            storeOriginalFormData();
            
            // Profile picture / initials
            const profileInitials = document.getElementById("profileInitials");
            if (user.profilePicture) {
                profilePicture.src = user.profilePicture;
                profilePicture.style.display = "block";
                if (profileInitials) profileInitials.style.display = "none";
            } else if (profileInitials) {
                const initials = ((firstName.charAt(0) || "") + (lastName.charAt(0) || "")).toUpperCase() || (username.charAt(0) || "?").toUpperCase();
                profileInitials.textContent = initials;
                profileInitials.style.display = "flex";
                profilePicture.style.display = "none";
            }
        }
        
        // Load friends
        await loadFriends();
        
        // Load notifications
        await loadNotifications();
        
    } catch (error) {
        console.error("Error loading profile:", error);
        alert("Error loading profile data");
    }
}

// Store original form data
function storeOriginalFormData() {
    const formData = new FormData(profileForm);
    originalFormData = {};
    for (let [key, value] of formData.entries()) {
        originalFormData[key] = value;
    }
}

// Profile picture upload
profilePictureInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            profilePicture.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});

// Save profile changes
profileForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const formData = new FormData(profileForm);
    const fields = {
        firstName: formData.get("firstName"),
        lastName: formData.get("lastName"),
        phone: formData.get("phone"),
        address: formData.get("address"),
        city: formData.get("city"),
        province: formData.get("province"),
        postalCode: formData.get("postalCode"),
        country: formData.get("country")
    };
    
    try {
        const result = await updateProfile(username, fields);
        if (result.status === "success") {
            alert("Profile updated successfully!");
            storeOriginalFormData();
            displayUsername.textContent = `${fields.firstName} ${fields.lastName}`.trim() || username;
        } else {
            alert(result.message || "Error saving profile changes");
        }
    } catch (error) {
        console.error("Error saving profile:", error);
        alert("Error saving profile changes");
    }
});

// Cancel button - reset form
cancelBtn.addEventListener("click", () => {
    if (confirm("Discard unsaved changes?")) {
        for (let [key, value] of Object.entries(originalFormData)) {
            const input = profileForm.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = value;
            }
        }
    }
});

// Load friends list
async function loadFriends() {
    try {
        const result = await getFriends(userId);
        const friends = (result.status === "success" && result.friends) ? result.friends : [];
        
        // Map backend shape to display shape
        const mapped = friends.map(f => ({
            id: f.friendshipId,
            username: f.friendUsername || "Unknown",
            friendsSince: f.since || new Date().toISOString()
        }));
        
        displayFriends(mapped);
    } catch (error) {
        console.error("Error loading friends:", error);
        friendsList.innerHTML = '<p class="empty-text">Error loading friends</p>';
    }
}

// Display friends
function displayFriends(friends) {
    if (!friends || friends.length === 0) {
        friendsList.innerHTML = '<p class="empty-text">No friends yet. Start by inviting someone!</p>';
        return;
    }
    
    friendsList.innerHTML = friends.map(friend => {
        const initials = friend.username.charAt(0).toUpperCase();
        const friendsSinceDate = new Date(friend.friendsSince).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        return `
            <div class="friend-item">
                <div class="friend-info">
                    <div class="friend-avatar">${initials}</div>
                    <div class="friend-details">
                        <h3>${friend.username}</h3>
                        <p>Friends since ${friendsSinceDate}</p>
                    </div>
                </div>
                <button class="remove-friend-btn" onclick="removeFriend(${friend.id})">Remove</button>
            </div>
        `;
    }).join('');
}

// Remove friend
window.removeFriend = async function(friendId) {
    if (confirm("Are you sure you want to remove this friend?")) {
        try {
            const result = await apiRemoveFriend(friendId, userId);
            if (result.status === "success") {
                loadFriends();
            } else {
                alert(result.message || "Error removing friend");
            }
        } catch (error) {
            console.error("Error removing friend:", error);
            alert("Error removing friend");
        }
    }
};

// Load notifications
async function loadNotifications(filter = "all") {
    try {
        const result = await getNotifications(userId);
        let notifications = [];
        
        if (result.status === "success" && result.notifications) {
            notifications = result.notifications.map(n => ({
                id: n.id,
                type: n.type || "event",
                title: n.title || "Notification",
                message: n.message || "",
                business: n.businessName || "",
                date: n.date || "",
                time: n.createdAt ? timeAgo(n.createdAt) : "",
                read: n.read || false,
                actions: n.read ? ["dismiss"] : ["view", "dismiss"]
            }));
        }
        
        // Filter notifications
        let filteredNotifications = notifications;
        if (filter !== "all") {
            filteredNotifications = notifications.filter(n => {
                if (filter === "reservations") return n.type === "reservation";
                if (filter === "deals") return n.type === "deal";
                if (filter === "events") return n.type === "event";
                return true;
            });
        }
        
        displayNotifications(filteredNotifications);
    } catch (error) {
        console.error("Error loading notifications:", error);
        notificationsList.innerHTML = '<p class="empty-text">No notifications yet</p>';
    }
}

function timeAgo(dateStr) {
    const now = new Date();
    const past = new Date(dateStr);
    const diffMs = now - past;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs} hour${diffHrs > 1 ? "s" : ""} ago`;
    const diffDays = Math.floor(diffHrs / 24);
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
}

// Display notifications
function displayNotifications(notifications) {
    if (!notifications || notifications.length === 0) {
        notificationsList.innerHTML = '<p class="empty-text">No notifications</p>';
        return;
    }
    
    notificationsList.innerHTML = notifications.map(notification => {
        const iconEmoji = {
            reservation: '<i class="fa-solid fa-calendar"></i>',
            deal: '<i class="fa-solid fa-tag"></i>',
            event: '<i class="fa-solid fa-champagne-glasses"></i>'
        }[notification.type] || '<i class="fa-solid fa-bell"></i>';
        
        const actionButtons = notification.actions.map(action => {
            if (action === "confirm") {
                return `<button class="confirm-btn" onclick="handleNotificationAction(${notification.id}, 'confirm')">Confirm</button>`;
            } else if (action === "view") {
                return `<button class="view-btn" onclick="handleNotificationAction(${notification.id}, 'view')">View Details</button>`;
            } else if (action === "dismiss") {
                return `<button class="dismiss-btn" onclick="handleNotificationAction(${notification.id}, 'dismiss')">Dismiss</button>`;
            }
            return '';
        }).join('');
        
        return `
            <div class="notification-item">
                <div class="notification-icon ${notification.type}">${iconEmoji}</div>
                <div class="notification-content">
                    <h4>${notification.title}</h4>
                    <p><strong>${notification.business}</strong></p>
                    <p>${notification.message}</p>
                    ${notification.date ? `<p><strong>${notification.date}</strong></p>` : ''}
                    ${notification.expiresAt ? `<p>${notification.expiresAt}</p>` : ''}
                    <span class="notification-time">${notification.time}</span>
                    <div class="notification-actions">
                        ${actionButtons}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Handle notification actions
window.handleNotificationAction = async function(notificationId, action) {
    if (action === "view") {
        // Mark as read, then stay on page (notification details are inline)
        try {
            await markNotificationRead(notificationId);
        } catch (e) {
            console.error("Error marking notification read:", e);
        }
        loadNotifications(currentFilter);
    } else if (action === "dismiss") {
        try {
            await markNotificationRead(notificationId);
            loadNotifications(currentFilter);
        } catch (e) {
            console.error("Error dismissing notification:", e);
        }
    }
};

// Tab filtering
let currentFilter = "all";
tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        // Update active tab
        tabBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        
        // Load filtered notifications
        currentFilter = btn.dataset.tab;
        loadNotifications(currentFilter);
    });
});

// Invite friend modal
openInviteModal.addEventListener("click", () => {
    inviteModal.classList.add("show");
});

closeModal.addEventListener("click", () => {
    inviteModal.classList.remove("show");
});

window.addEventListener("click", (e) => {
    if (e.target === inviteModal) {
        inviteModal.classList.remove("show");
    }
});

inviteForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const friendEmail = document.getElementById("friendEmail").value;
    
    try {
        // Search for the user by email/username first
        const searchResult = await searchUsers(friendEmail, userId);
        if (searchResult.status === "success" && searchResult.users && searchResult.users.length > 0) {
            const targetUser = searchResult.users[0];
            const reqResult = await sendFriendRequest(userId, targetUser.id);
            if (reqResult.status === "success") {
                alert(`Friend request sent to ${targetUser.username}!`);
                inviteModal.classList.remove("show");
                inviteForm.reset();
            } else {
                alert(reqResult.message || "Could not send friend request.");
            }
        } else {
            alert("No user found with that email/username. They may need to create an account first.");
        }
    } catch (error) {
        console.error("Error sending invite:", error);
        alert("Error sending invitation");
    }
});

// Initialize on page load
initProfile();
setupUpgradeSection();

function setupUpgradeSection() {
    const section = document.getElementById("upgrade-section");
    const upgradeForm = document.getElementById("upgradeForm");
    const statusEl = document.getElementById("upgradeStatus");
    if (!section || !upgradeForm) return;

    // Show section only for non-business users
    const roles = session.roles || ["user"];
    if (roles.includes("business") || roles.includes("admin")) {
        section.style.display = "none";
        return;
    }
    section.style.display = "block";

    upgradeForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const btn = document.getElementById("upgradeBtn");
        btn.disabled = true;
        btn.textContent = "Verifying...";
        statusEl.textContent = "";

        const bizName = document.getElementById("bizName").value.trim();
        const bizAddress = document.getElementById("bizAddress").value.trim();
        const bizPhone = document.getElementById("bizPhone").value.trim();
        const bizCategory = document.getElementById("bizCategory").value;
        const bizIdInput = document.getElementById("upgradeBizId");
        const bizId = bizIdInput ? parseInt(bizIdInput.value) || null : null;

        if (!bizName || !bizAddress || !bizPhone || !bizCategory) {
            statusEl.textContent = "Please fill in all required fields.";
            statusEl.style.color = "#c0392b";
            btn.disabled = false;
            btn.textContent = "Verify & Upgrade";
            return;
        }

        try {
            const result = await upgradeToBusinessOwner(userId, bizName, bizId, {
                address: bizAddress,
                phone: bizPhone,
                category: bizCategory
            });
            if (result.status === "success") {
                statusEl.textContent = "Business verified! Your account has been upgraded. Reloading...";
                statusEl.style.color = "#27ae60";
                // Update session
                const updatedSession = { ...session, roles: result.user.roles, businessId: result.user.businessId };
                localStorage.setItem("session", JSON.stringify(updatedSession));
                setTimeout(() => window.location.reload(), 1500);
            } else {
                statusEl.textContent = result.message || "Verification failed.";
                statusEl.style.color = "#c0392b";
                btn.disabled = false;
                btn.textContent = "Verify & Upgrade";
            }
        } catch (err) {
            statusEl.textContent = "Error: " + (err.message || "Unknown error");
            statusEl.style.color = "#c0392b";
            btn.disabled = false;
            btn.textContent = "Verify & Upgrade";
        }
    });
}