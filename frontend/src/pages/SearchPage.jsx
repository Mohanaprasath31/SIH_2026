import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search,
    Loader2,
    FileQuestion,
    Camera,
    ArrowRight,
    ShieldCheck
} from 'lucide-react';

import { searchVehicles, getCameras } from '../api/client';


export const SearchPage = () => {

    const [query, setQuery] = useState('TN');
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [results, setResults] = useState([]);
    const [cameraMap, setCameraMap] = useState({});

    const navigate = useNavigate();

    // Used to prevent an older search request
    // from overwriting a newer search result.
    const searchRequestId = useRef(0);


    // ============================================================
    // LOAD CAMERA DETAILS
    // ============================================================

    useEffect(() => {

        getCameras()
            .then(cams => {

                if (Array.isArray(cams)) {

                    const map = {};

                    cams.forEach(camera => {

                        map[camera.camera_id] =
                            camera.name ||
                            camera.road ||
                            'ANPR Camera';

                    });

                    setCameraMap(map);
                }
            })
            .catch(err => {

                console.warn(
                    'Failed to load camera map:',
                    err
                );

            });

    }, []);


    // ============================================================
    // SEARCH
    // ============================================================

    const handleSearch = async (searchQuery = query) => {

        const term = searchQuery.trim();

        if (!term) {
            return;
        }

        // Generate a unique ID for this request.
        // Only the latest request is allowed to update the UI.
        const requestId = ++searchRequestId.current;

        setLoading(true);
        setHasSearched(true);

        try {

            const data = await searchVehicles(term);

            // ----------------------------------------------------
            // IMPORTANT:
            // Ignore stale responses.
            // ----------------------------------------------------

            if (requestId !== searchRequestId.current) {

                console.log(
                    '[Search] Ignoring stale search response:',
                    term
                );

                return;
            }


            let vehiclesList = [];


            // ====================================================
            // VEHICLES RETURNED FROM BACKEND
            // ====================================================

            if (
                data &&
                Array.isArray(data.vehicles) &&
                data.vehicles.length > 0
            ) {

                // Group observations by plate.
                const obsByVehicle = {};

                (data.recent_observations || []).forEach(obs => {

                    const plate = obs.plate_number;

                    if (!plate) {
                        return;
                    }

                    if (!obsByVehicle[plate]) {
                        obsByVehicle[plate] = [];
                    }

                    obsByVehicle[plate].push(obs);

                });


                vehiclesList = data.vehicles
                    .filter(vehicle => {

                        // Never allow a vehicle without a
                        // real backend vehicle_id.
                        return Boolean(vehicle.vehicle_id);

                    })
                    .map(vehicle => {

                        const plate =
                            vehicle.normalized_plate;

                        const plateObs =
                            obsByVehicle[plate] || [];


                        // Extract camera sequence.
                        const cameraSeq = plateObs
                            .map(obs => obs.camera_id)
                            .filter(Boolean);


                        return {

                            vehicle_id:
                                vehicle.vehicle_id,

                            normalized_plate:
                                vehicle.normalized_plate,

                            first_seen:
                                vehicle.first_seen,

                            last_seen:
                                vehicle.last_seen,

                            observation_count:
                                plateObs.length ||
                                vehicle.observation_count ||
                                0,

                            camera_sequence:
                                cameraSeq

                        };

                    });

            }


            // ====================================================
            // OBSERVATION FALLBACK
            // ====================================================
            //
            // We only use this when the backend does not return
            // vehicle rows.
            //
            // IMPORTANT:
            // We do NOT create fake vehicle IDs anymore.
            //
            // If observations do not contain a real vehicle_id,
            // they cannot safely open the trajectory page.
            // ====================================================

            else if (
                data &&
                Array.isArray(data.recent_observations) &&
                data.recent_observations.length > 0
            ) {

                const obsGrouped = {};

                data.recent_observations.forEach(obs => {

                    const plate =
                        obs.plate_number;

                    if (!plate) {
                        return;
                    }

                    if (!obsGrouped[plate]) {

                        obsGrouped[plate] = {

                            plate,
                            obsList: []

                        };

                    }

                    obsGrouped[plate]
                        .obsList
                        .push(obs);

                });


                vehiclesList = Object.values(
                    obsGrouped
                )
                    .filter(group => {

                        // Require at least one real vehicle ID.
                        return group.obsList.some(
                            obs => Boolean(obs.vehicle_id)
                        );

                    })
                    .map(group => {

                        const sortedObs =
                            [...group.obsList]
                                .sort(
                                    (a, b) =>
                                        new Date(a.timestamp) -
                                        new Date(b.timestamp)
                                );


                        const cameraSeq =
                            sortedObs
                                .map(obs => obs.camera_id)
                                .filter(Boolean);


                        const realVehicle =
                            sortedObs.find(
                                obs =>
                                    Boolean(
                                        obs.vehicle_id
                                    )
                            );


                        return {

                            vehicle_id:
                                realVehicle.vehicle_id,

                            normalized_plate:
                                group.plate,

                            first_seen:
                                sortedObs[0]?.timestamp ||
                                null,

                            last_seen:
                                sortedObs[
                                    sortedObs.length - 1
                                ]?.timestamp ||
                                null,

                            observation_count:
                                sortedObs.length,

                            camera_sequence:
                                cameraSeq

                        };

                    });

            }


            // ====================================================
            // UPDATE RESULTS
            // ====================================================

            setResults(vehiclesList);

        }
        catch (err) {

            // Ignore errors from stale requests.
            if (
                requestId !==
                searchRequestId.current
            ) {
                return;
            }

            console.error(
                'Search request failed:',
                err
            );

            setResults([]);

        }
        finally {

            // Only the latest request controls loading state.
            if (
                requestId ===
                searchRequestId.current
            ) {

                setLoading(false);

            }

        }

    };


    // ============================================================
    // FORM SUBMIT
    // ============================================================

    const handleFormSubmit = (e) => {

        e.preventDefault();

        handleSearch(query);

    };


    // ============================================================
    // OPEN TRAJECTORY
    // ============================================================

    const handleRowClick = (vehicleId) => {

        if (!vehicleId) {

            console.error(
                '[Search] Cannot open trajectory: missing vehicle ID.'
            );

            return;

        }

        console.log(
            '[Search] Opening trajectory for vehicle:',
            vehicleId
        );

        navigate(
            `/trajectory/${encodeURIComponent(vehicleId)}`
        );

    };


    // ============================================================
    // DATE FORMATTER
    // ============================================================

    const formatDate = (dateStr) => {

        if (!dateStr) {
            return 'N/A';
        }

        try {

            const d = new Date(dateStr);

            return `${d.toLocaleDateString()} ${d.toLocaleTimeString(
                [],
                {
                    hour: '2-digit',
                    minute: '2-digit'
                }
            )}`;

        }
        catch {

            return dateStr;

        }

    };


    // ============================================================
    // UI
    // ============================================================

    return (

        <div className="page-container">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header">

                <div>

                    <h1 className="page-title">

                        <Search
                            size={24}
                            color="#06b6d4"
                        />

                        Vehicle Search & OCR Plate Lookup

                    </h1>


                    <p className="page-subtitle">

                        Search normalized registration
                        numbers across ANPR camera records
                        & trajectory logs.

                    </p>

                </div>

            </div>


            {/* ==================================================
                SEARCH INPUT
            ================================================== */}

            <div className="ops-card">

                <form
                    onSubmit={handleFormSubmit}
                    className="search-box"
                >

                    <div className="search-input-wrapper">

                        <Search
                            size={18}
                            className="search-input-icon"
                        />

                        <input
                            type="text"
                            placeholder="Search by license plate..."
                            className="ops-input"
                            value={query}
                            onChange={(e) =>
                                setQuery(e.target.value)
                            }
                        />

                    </div>


                    <button
                        type="submit"
                        className="ops-button"
                        disabled={loading}
                    >

                        {loading ? (

                            <Loader2
                                size={16}
                                className="animate-spin"
                            />

                        ) : (

                            <Search size={16} />

                        )}

                        Search Database

                    </button>

                </form>

            </div>


            {/* ==================================================
                RESULTS
            ================================================== */}

            <div className="ops-card">

                {/* Loading */}

                {loading && (

                    <div className="state-container">

                        <div className="state-icon-box">

                            <Loader2
                                size={26}
                                className="animate-spin"
                            />

                        </div>


                        <h3 className="state-title">

                            Querying ANPR Database...

                        </h3>


                        <p className="state-desc">

                            Scanning indexed vehicle
                            observations and spatial camera
                            records for "{query}".

                        </p>

                    </div>

                )}


                {/* Empty */}

                {!loading &&
                    hasSearched &&
                    results.length === 0 && (

                        <div className="state-container">

                            <div
                                className="state-icon-box"
                                style={{
                                    color: '#f59e0b',
                                    backgroundColor:
                                        'rgba(245, 158, 11, 0.12)',
                                    borderColor:
                                        'rgba(245, 158, 11, 0.35)'
                                }}
                            >

                                <FileQuestion size={26} />

                            </div>


                            <h3 className="state-title">

                                No Matching Vehicles Found

                            </h3>


                            <p className="state-desc">

                                No ANPR records matched
                                registration plate "{query}".

                            </p>

                        </div>

                    )}


                {/* Results */}

                {!loading &&
                    results.length > 0 && (

                        <div className="search-table-wrapper">

                            <table className="ops-table">

                                <thead>

                                    <tr>

                                        <th>
                                            Plate Number
                                        </th>

                                        <th>
                                            First Seen
                                        </th>

                                        <th>
                                            Last Seen
                                        </th>

                                        <th>
                                            Observation Count
                                        </th>

                                        <th>
                                            Ordered Camera Sequence
                                        </th>

                                        <th
                                            style={{
                                                textAlign:
                                                    'right'
                                            }}
                                        >
                                            Action
                                        </th>

                                    </tr>

                                </thead>


                                <tbody>

                                    {results.map(row => (

                                        <tr
                                            key={
                                                row.vehicle_id +
                                                row.normalized_plate
                                            }
                                            className="ops-table-row"
                                            onClick={() =>
                                                handleRowClick(
                                                    row.vehicle_id
                                                )
                                            }
                                            title="Click to view full vehicle trajectory"
                                        >

                                            {/* Plate */}

                                            <td>

                                                <div className="plate-badge">

                                                    <ShieldCheck
                                                        size={14}
                                                        color="#06b6d4"
                                                    />

                                                    {
                                                        row.normalized_plate
                                                    }

                                                </div>

                                            </td>


                                            {/* First Seen */}

                                            <td
                                                style={{
                                                    fontFamily:
                                                        'var(--font-mono)',
                                                    fontSize:
                                                        '0.8125rem'
                                                }}
                                            >

                                                {
                                                    formatDate(
                                                        row.first_seen
                                                    )
                                                }

                                            </td>


                                            {/* Last Seen */}

                                            <td
                                                style={{
                                                    fontFamily:
                                                        'var(--font-mono)',
                                                    fontSize:
                                                        '0.8125rem'
                                                }}
                                            >

                                                {
                                                    formatDate(
                                                        row.last_seen
                                                    )
                                                }

                                            </td>


                                            {/* Observation Count */}

                                            <td>

                                                <span
                                                    style={{
                                                        fontFamily:
                                                            'var(--font-mono)',
                                                        fontWeight:
                                                            700,
                                                        color:
                                                            'var(--ops-accent)'
                                                    }}
                                                >

                                                    {
                                                        row.observation_count
                                                    }

                                                    {' '}captures

                                                </span>

                                            </td>


                                            {/* Camera Sequence */}

                                            <td>

                                                <div className="camera-chips-container">

                                                    {row.camera_sequence
                                                        .slice(0, 4)
                                                        .map(
                                                            (
                                                                camId,
                                                                cIdx
                                                            ) => {

                                                                const camName =
                                                                    cameraMap[
                                                                        camId
                                                                    ] ||
                                                                    `Cam #${
                                                                        cIdx +
                                                                        1
                                                                    }`;


                                                                return (

                                                                    <span
                                                                        key={
                                                                            camId +
                                                                            cIdx
                                                                        }
                                                                        className="camera-chip"
                                                                    >

                                                                        <Camera
                                                                            size={
                                                                                11
                                                                            }
                                                                        />

                                                                        {
                                                                            camName
                                                                        }

                                                                    </span>

                                                                );

                                                            }
                                                        )}


                                                    {row.camera_sequence
                                                        .length >
                                                        4 && (

                                                        <span
                                                            className="camera-chip"
                                                            style={{
                                                                opacity:
                                                                    0.8
                                                            }}
                                                        >

                                                            +
                                                            {
                                                                row
                                                                    .camera_sequence
                                                                    .length -
                                                                4
                                                            }

                                                            {' '}more

                                                        </span>

                                                    )}

                                                </div>

                                            </td>


                                            {/* Action */}

                                            <td
                                                style={{
                                                    textAlign:
                                                        'right'
                                                }}
                                            >

                                                <span
                                                    style={{
                                                        color:
                                                            '#06b6d4',
                                                        display:
                                                            'inline-flex',
                                                        alignItems:
                                                            'center',
                                                        gap:
                                                            '0.25rem',
                                                        fontSize:
                                                            '0.75rem',
                                                        fontFamily:
                                                            'var(--font-mono)'
                                                    }}
                                                >

                                                    Trajectory

                                                    <ArrowRight
                                                        size={14}
                                                    />

                                                </span>

                                            </td>

                                        </tr>

                                    ))}

                                </tbody>

                            </table>

                        </div>

                    )}

            </div>

        </div>

    );

};


export default SearchPage;