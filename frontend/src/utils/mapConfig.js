/**
 * Shared Map Configuration Utility for MapLibre GL JS
 */

export const MAP_MAX_ZOOM = 19;

/**
 * Returns OpenFreeMap's "Liberty" vector map style URL.
 * Free vector tile style containing complete road networks, landuse, buildings, and labels.
 * Requires no API key.
 */
export function getMapStyle() {
    return 'https://tiles.openfreemap.org/styles/liberty';
}

export const DEFAULT_MAP_CONFIG = {
    maxZoom: MAP_MAX_ZOOM,
    minZoom: 0,
};

/**
 * Dynamic Style Recoloring Helper
 * Overrides paint properties of OpenFreeMap Liberty base layers to match Google Maps' exact palette:
 * - Water / Ocean: #a2daf2 (Google Maps signature light blue)
 * - General Land / Background: #e8efd8 (light pastel green landmass)
 * - Parks & Forests: #c8e6a0 (richer vegetation green)
 * - Highways & Major Roads: #f8c967 (subtle Google yellow)
 * - Minor & Local Streets: #ffffff (clean white fills)
 * - Place Labels: #4a4a4a (dark gray with white halo for high legibility)
 */
export function recolorStyleToGoogleMaps(map) {
    if (!map) return;

    const applyColors = () => {
        try {
            const style = map.getStyle();
            if (!style || !style.layers) return;

            style.layers.forEach((layer) => {
                const id = layer.id;
                const type = layer.type;

                // 1. Background & General Land
                if (type === 'background') {
                    map.setPaintProperty(id, 'background-color', '#e8efd8');
                } else if (type === 'fill') {
                    // 2. Water / Ocean / Sea / Lakes
                    if (id.includes('water') || id.includes('ocean') || id.includes('sea') || id.includes('lake')) {
                        map.setPaintProperty(id, 'fill-color', '#a2daf2');
                    }
                    // 3. Parks & Forested / Greenery Areas
                    else if (
                        id.includes('park') ||
                        id.includes('wood') ||
                        id.includes('forest') ||
                        id.includes('grass') ||
                        id.includes('green') ||
                        id.includes('cemetery') ||
                        id.includes('pitch') ||
                        id.includes('reserve') ||
                        id.includes('farmland') ||
                        id.includes('meadow')
                    ) {
                        map.setPaintProperty(id, 'fill-color', '#c8e6a0');
                    }
                    // 4. General Landcover & Landuse
                    else if (id.includes('landcover') || id.includes('landuse') || id.includes('sand')) {
                        map.setPaintProperty(id, 'fill-color', '#e4ebcf');
                    }
                    // 5. Buildings
                    else if (id.includes('building')) {
                        map.setPaintProperty(id, 'fill-color', '#dbe3cb');
                    }
                }
                // 6. Lines (Waterways, Roads, Highways)
                else if (type === 'line') {
                    if (id.includes('water') || id.includes('river') || id.includes('stream')) {
                        map.setPaintProperty(id, 'line-color', '#89cef1');
                    }
                    // 7. Highways & Major Roads (subtle Google yellow)
                    else if (
                        id.includes('motorway') ||
                        id.includes('trunk') ||
                        id.includes('primary')
                    ) {
                        if (!id.includes('casing')) {
                            map.setPaintProperty(id, 'line-color', '#f8c967');
                        }
                    }
                    // 8. Minor Streets & Local Roads (white/light gray)
                    else if (
                        id.includes('secondary') ||
                        id.includes('tertiary') ||
                        id.includes('street') ||
                        id.includes('service') ||
                        id.includes('residential') ||
                        id.includes('link')
                    ) {
                        if (!id.includes('casing')) {
                            map.setPaintProperty(id, 'line-color', '#ffffff');
                        }
                    }
                }
                // 9. Place Labels & Typography (dark gray with crisp white halo)
                else if (type === 'symbol') {
                    if (map.getLayoutProperty(id, 'text-field')) {
                        map.setPaintProperty(id, 'text-color', '#4a4a4a');
                        map.setPaintProperty(id, 'text-halo-color', '#ffffff');
                        map.setPaintProperty(id, 'text-halo-width', 1.5);
                    }
                }
            });
        } catch (err) {
            console.warn('Error recoloring map style layers:', err);
        }
    };

    if (map.isStyleLoaded()) {
        applyColors();
    } else {
        map.once('style.load', applyColors);
    }
}
