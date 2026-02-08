import { getSession, requireAuth, logout, getUserProfile } from "../api-client.js";

// Check authentication
if (!requireAuth()) {
    throw new Error("Not authenticated");
}

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
const logoutBtn = document.getElementById("logoutBtn");
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
            }
            
            // Populate form
            document.getElementById("firstName").value = user.firstName || "";
            document.getElementById("lastName").value = user.lastName || "";
            document.getElementById("email").value = user.email || "";
            document.getElementById("phone").value = user.phone || "";
            document.getElementById("address").value = user.address || "";
            document.getElementById("city").value = user.city || "";
            document.getElementById("province").value = user.province || "";
            document.getElementById("postalCode").value = user.postalCode || "";
            document.getElementById("country").value = user.country || "";
            
            // Store original data
            storeOriginalFormData();
            
            // Load profile picture if available
            if (user.profilePicture) {
                profilePicture.src = user.profilePicture;
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
        // Preview the image
        const reader = new FileReader();
        reader.onload = function(e) {
            profilePicture.src = e.target.result;
        };
        reader.readAsDataURL(file);
        
        // In a real implementation, upload to server here
        // const formData = new FormData();
        // formData.append("profilePicture", file);
        // const response = await fetch(`/api/users/${userId}/profile-picture`, {
        //     method: "POST",
        //     body: formData
        // });
        
        alert("Profile picture updated! (Note: Upload to server would happen here)");
    }
});

// Save profile changes
profileForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const formData = new FormData(profileForm);
    const profileData = {
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
        // In a real implementation, send to server
        // const response = await fetch(`http://127.0.0.1:5001/api/users/${userId}`, {
        //     method: "PUT",
        //     headers: { "Content-Type": "application/json" },
        //     body: JSON.stringify(profileData)
        // });
        
        alert("Profile updated successfully!");
        storeOriginalFormData();
        
        // Update display name
        displayUsername.textContent = `${profileData.firstName} ${profileData.lastName}`.trim() || username;
        
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
        // Mock friends data - replace with actual API call
        const mockFriends = [
            {
                id: 1,
                username: "sarah_johnson",
                email: "sarah@example.com",
                friendsSince: "2023-08-15"
            },
            {
                id: 2,
                username: "mike_chen",
                email: "mike@example.com",
                friendsSince: "2023-11-22"
            },
            {
                id: 3,
                username: "emma_davis",
                email: "emma@example.com",
                friendsSince: "2024-01-10"
            }
        ];
        
        // In real implementation:
        // const response = await fetch(`http://127.0.0.1:5001/api/friends?user_id=${userId}`);
        // const friends = await response.json();
        
        displayFriends(mockFriends);
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
            // In real implementation:
            // await fetch(`http://127.0.0.1:5001/api/friends/${friendId}?user_id=${userId}`, {
            //     method: "DELETE"
            // });
            
            alert("Friend removed");
            loadFriends();
        } catch (error) {
            console.error("Error removing friend:", error);
            alert("Error removing friend");
        }
    }
};

// Load notifications
async function loadNotifications(filter = "all") {
    try {
        // Mock notifications data - replace with actual API call
        const mockNotifications = [
            {
                id: 1,
                type: "reservation",
                title: "Reservation Confirmed",
                message: "Your table for 4 at Luigi's Italian Restaurant is confirmed",
                business: "Luigi's Italian Restaurant",
                date: "Feb 15, 2026 at 7:00 PM",
                time: "2 hours ago",
                actions: ["confirm", "view"]
            },
            {
                id: 2,
                type: "deal",
                title: "New Deal Available",
                message: "50% off appetizers at The Sushi Place",
                business: "The Sushi Place",
                expiresAt: "Valid until Feb 10, 2026",
                time: "5 hours ago",
                actions: ["view", "dismiss"]
            },
            {
                id: 3,
                type: "event",
                title: "Upcoming Event",
                message: "Live Jazz Night this Friday",
                business: "Blue Note Café",
                date: "Feb 7, 2026 at 8:00 PM",
                time: "1 day ago",
                actions: ["view", "dismiss"]
            },
            {
                id: 4,
                type: "reservation",
                title: "Reservation Reminder",
                message: "Don't forget your reservation tomorrow!",
                business: "Thai Spice Kitchen",
                date: "Feb 2, 2026 at 6:30 PM",
                time: "6 hours ago",
                actions: ["confirm", "view"]
            }
        ];
        
        // Filter notifications
        let filteredNotifications = mockNotifications;
        if (filter !== "all") {
            filteredNotifications = mockNotifications.filter(n => {
                if (filter === "reservations") return n.type === "reservation";
                if (filter === "deals") return n.type === "deal";
                if (filter === "events") return n.type === "event";
                return true;
            });
        }
        
        displayNotifications(filteredNotifications);
    } catch (error) {
        console.error("Error loading notifications:", error);
        notificationsList.innerHTML = '<p class="empty-text">Error loading notifications</p>';
    }
}

// Display notifications
function displayNotifications(notifications) {
    if (!notifications || notifications.length === 0) {
        notificationsList.innerHTML = '<p class="empty-text">No notifications</p>';
        return;
    }
    
    notificationsList.innerHTML = notifications.map(notification => {
        const iconEmoji = {
            reservation: "📅",
            deal: "💰",
            event: "🎉"
        }[notification.type] || "🔔";
        
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
    if (action === "confirm") {
        alert("Reservation confirmed!");
        // In real implementation: update server
    } else if (action === "view") {
        alert("Viewing details... (would navigate to business/event page)");
        // In real implementation: navigate to relevant page
    } else if (action === "dismiss") {
        if (confirm("Dismiss this notification?")) {
            // In real implementation: mark as read on server
            loadNotifications(currentFilter);
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
    const message = document.getElementById("inviteMessage").value;
    
    try {
        // In real implementation: send invite via API
        // const response = await fetch("http://127.0.0.1:5001/api/friends/invite", {
        //     method: "POST",
        //     headers: { "Content-Type": "application/json" },
        //     body: JSON.stringify({
        //         fromUserId: userId,
        //         toEmail: friendEmail,
        //         message: message
        //     })
        // });
        
        alert(`Invitation sent to ${friendEmail}!`);
        inviteModal.classList.remove("show");
        inviteForm.reset();
        
    } catch (error) {
        console.error("Error sending invite:", error);
        alert("Error sending invitation");
    }
});

// Logout
logoutBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    if (confirm("Are you sure you want to logout?")) {
        await logout();
    }
});

// Initialize on page load
initProfile();