const LOCATION_STORAGE_KEY = "candyland_selected_location";

export function saveSelectedLocation(location) {
    sessionStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(location));
}

export function getSelectedLocation() {
    const value = sessionStorage.getItem(LOCATION_STORAGE_KEY);

    if (!value) {
        return null;
    }

    try {
        return JSON.parse(value);
    } catch {
        sessionStorage.removeItem(LOCATION_STORAGE_KEY);
        return null;
    }
}

export function clearSelectedLocation() {
    sessionStorage.removeItem(LOCATION_STORAGE_KEY);
}
