import { requireAuth, logout, getSession, searchUsers, sendFriendRequest, getFriendRequests, acceptFriendRequest, rejectFriendRequest, getFriends, removeFriend, getFriendActivity, getBusinessById } from "./api-client.js";

if (!requireAuth()) {
    throw new Error("Authentication required");
}

const session = getSession();
const userId = session.userId;

const userSearchInput = document.getElementById("user-search");
const userSearchResults = document.getElementById("user-search-results");
const pendingRequestsEl = document.getElementById("pending-requests");
const friendsListEl = document.getElementById("friends-list");
const activityFeedEl = document.getElementById("activity-feed");
const logoutBtn = document.getElementById("logout-btn");

let searchTimeout = null;

async function loadFriendsData() {
    await Promise.all([
        loadPendingRequests(),
        loadFriendsList(),
        loadActivity(),
    ]);
}

async function loadPendingRequests() {
    try {
        const result = await getFriendRequests(userId);
        if (result.status === "success") {
            if (result.pending.length === 0) {
                pendingRequestsEl.innerHTML = '<p class="empty-text">No pending requests</p>';
                return;
            }

            pendingRequestsEl.innerHTML = result.pending.map(r => `
                <div class="request-item" data-request-id="${r.requestId}">
                    <span class="request-username">${r.fromUsername}</span>
                    <div class="request-actions">
                        <button class="accept-btn" data-id="${r.requestId}">Accept</button>
                        <button class="reject-btn" data-id="${r.requestId}">Reject</button>
                    </div>
                </div>
            `).join("");

            pendingRequestsEl.querySelectorAll(".accept-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const result = await acceptFriendRequest(parseInt(btn.dataset.id), userId);
                    if (result.status === "success") {
                        loadFriendsData();
                    }
                });
            });

            pendingRequestsEl.querySelectorAll(".reject-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const result = await rejectFriendRequest(parseInt(btn.dataset.id), userId);
                    if (result.status === "success") {
                        loadFriendsData();
                    }
                });
            });
        }
    } catch (error) {
        console.error("Error loading requests:", error);
    }
}

async function loadFriendsList() {
    try {
        const result = await getFriends(userId);
        if (result.status === "success") {
            if (result.friends.length === 0) {
                friendsListEl.innerHTML = '<p class="empty-text">No friends yet. Search for users above.</p>';
                return;
            }

            friendsListEl.innerHTML = result.friends.map(f => `
                <div class="friend-item" data-friendship-id="${f.friendshipId}">
                    <div class="friend-info">
                        <span class="friend-username">${f.friendUsername}</span>
                        <span class="friend-since">Friends since ${new Date(f.since).toLocaleDateString()}</span>
                    </div>
                    <button class="remove-friend-btn" data-id="${f.friendshipId}">Remove</button>
                </div>
            `).join("");

            friendsListEl.querySelectorAll(".remove-friend-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const result = await removeFriend(parseInt(btn.dataset.id), userId);
                    if (result.status === "success") {
                        loadFriendsData();
                    }
                });
            });
        }
    } catch (error) {
        console.error("Error loading friends:", error);
    }
}

async function loadActivity() {
    try {
        const result = await getFriendActivity(userId);
        if (result.status === "success") {
            if (result.activity.length === 0) {
                activityFeedEl.innerHTML = '<p class="empty-text">No recent activity from friends.</p>';
                return;
            }

            activityFeedEl.innerHTML = "";
            for (const item of result.activity) {
                let businessName = `Business #${item.businessID}`;
                try {
                    const biz = await getBusinessById(item.businessID);
                    if (biz.status === "success" && biz.business) {
                        businessName = biz.business.name;
                    }
                } catch (e) { /* use default */ }

                const stars = "★".repeat(item.rating) + "☆".repeat(5 - item.rating);
                const date = new Date(item.createdAt).toLocaleDateString();

                const activityItem = document.createElement("div");
                activityItem.className = "activity-item";
                activityItem.innerHTML = `
                    <div class="activity-header">
                        <span class="activity-username">${item.username}</span>
                        <span class="activity-date">${date}</span>
                    </div>
                    <div class="activity-business">${businessName}</div>
                    <div class="activity-rating">${stars}</div>
                    <div class="activity-content">${item.review || ""}</div>
                `;
                activityFeedEl.appendChild(activityItem);
            }
        }
    } catch (error) {
        console.error("Error loading activity:", error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadFriendsData();

    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logout();
        });
    }

    // User search
    userSearchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        const query = userSearchInput.value.trim();

        if (query.length < 2) {
            userSearchResults.classList.remove("active");
            return;
        }

        searchTimeout = setTimeout(async () => {
            try {
                const result = await searchUsers(query, userId);
                if (result.status === "success" && result.users.length > 0) {
                    userSearchResults.innerHTML = result.users.map(u => `
                        <div class="search-result-item">
                            <span>${u.username}</span>
                            <button class="add-friend-btn" data-user-id="${u.id}">Add Friend</button>
                        </div>
                    `).join("");
                    userSearchResults.classList.add("active");

                    userSearchResults.querySelectorAll(".add-friend-btn").forEach(btn => {
                        btn.addEventListener("click", async () => {
                            const result = await sendFriendRequest(userId, parseInt(btn.dataset.userId));
                            if (result.status === "success") {
                                btn.textContent = "Sent";
                                btn.disabled = true;
                                btn.style.background = "#ccc";
                            } else {
                                alert(result.message);
                            }
                        });
                    });
                } else {
                    userSearchResults.innerHTML = '<div class="search-result-item"><span>No users found</span></div>';
                    userSearchResults.classList.add("active");
                }
            } catch (error) {
                console.error("Search error:", error);
            }
        }, 300);
    });

    // Close search results when clicking outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".search-section")) {
            userSearchResults.classList.remove("active");
        }
    });
});
