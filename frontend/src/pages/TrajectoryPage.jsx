import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
    Navigation,
    Clock,
    MapPin,
    Gauge,
    ShieldCheck,
    ArrowLeft,
    Loader2,
    FileQuestion,
    Calendar
} from 'lucide-react';

import { getVehicleTrajectory, getCameras } from '../api/client';
import { TrajectoryMap } from '../components/TrajectoryMap';


export const TrajectoryPage = () => {

    const { vehicleId } = useParams();

    const [trajectory, setTrajectory] = useState(null);
    const [cameraMap, setCameraMap] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);


    // =========================================================
    // LOAD DATA
    // =========================================================

    useEffect(() => {

        // -----------------------------------------------------
        // LOAD CAMERA INFORMATION
        // -----------------------------------------------------

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
                    'Failed to load cameras for trajectory page:',
                    err
                );

            });


        // -----------------------------------------------------
        // VALIDATE VEHICLE ID
        // -----------------------------------------------------

        if (!vehicleId) {

            setLoading(false);
            return;
        }


        setLoading(true);
        setError(null);


        // -----------------------------------------------------
        // LOAD VEHICLE TRAJECTORY
        // -----------------------------------------------------

        getVehicleTrajectory(vehicleId)

            .then(data => {

                console.log(
                    '[TrajectoryPage] API response:',
                    data
                );


                // =================================================
                // ARRAY RESPONSE
                // =================================================

                if (
                    Array.isArray(data) &&
                    data.length > 0
                ) {

                    // ---------------------------------------------
                    // Find trajectories with valid average speed
                    // ---------------------------------------------

                    const validTrajectories =
                        data.filter(item => {

                            return (
                                item &&
                                item.trajectory_id &&
                                item.average_speed !== null &&
                                item.average_speed !== undefined &&
                                !Number.isNaN(
                                    Number(item.average_speed)
                                )
                            );

                        });


                    let selectedTrajectory = null;


                    // ---------------------------------------------
                    // Prefer newest trajectory with speed
                    // ---------------------------------------------

                    if (
                        validTrajectories.length > 0
                    ) {

                        selectedTrajectory =
                            [...validTrajectories].sort(
                                (a, b) => {

                                    const dateA =
                                        new Date(
                                            a.created_at ||
                                            a.start_time ||
                                            0
                                        ).getTime();

                                    const dateB =
                                        new Date(
                                            b.created_at ||
                                            b.start_time ||
                                            0
                                        ).getTime();

                                    return dateB - dateA;
                                }
                            )[0];

                    }


                    // ---------------------------------------------
                    // Fallback to newest trajectory
                    // ---------------------------------------------

                    else {

                        selectedTrajectory =
                            [...data].sort(
                                (a, b) => {

                                    const dateA =
                                        new Date(
                                            a.created_at ||
                                            a.start_time ||
                                            0
                                        ).getTime();

                                    const dateB =
                                        new Date(
                                            b.created_at ||
                                            b.start_time ||
                                            0
                                        ).getTime();

                                    return dateB - dateA;
                                }
                            )[0];

                    }


                    console.log(
                        '[TrajectoryPage] Selected trajectory:',
                        selectedTrajectory
                    );


                    setTrajectory(
                        selectedTrajectory
                    );

                }


                // =================================================
                // SINGLE OBJECT RESPONSE
                // =================================================

                else if (
                    data &&
                    data.trajectory_id
                ) {

                    console.log(
                        '[TrajectoryPage] Single trajectory:',
                        data
                    );

                    setTrajectory(data);

                }


                // =================================================
                // NO TRAJECTORY
                // =================================================

                else {

                    setTrajectory(null);

                }

            })

            .catch(err => {

                console.error(
                    'Failed to load vehicle trajectory:',
                    err
                );


                setError(
                    'Failed to load vehicle trajectory record.'
                );


                setTrajectory(null);

            })

            .finally(() => {

                setLoading(false);

            });

    }, [vehicleId]);


    // =========================================================
    // DATE FORMATTER
    // =========================================================

    const formatDate = (dateStr) => {

        if (!dateStr) {

            return 'N/A';

        }


        try {

            const date = new Date(dateStr);


            return `${date.toLocaleDateString()} ${date.toLocaleTimeString(
                [],
                {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                }
            )}`;

        }

        catch {

            return dateStr;

        }

    };


    // =========================================================
    // DURATION FORMATTER
    // =========================================================

    const formatDuration = (seconds) => {

        if (
            seconds === null ||
            seconds === undefined ||
            Number.isNaN(Number(seconds))
        ) {

            return 'N/A';

        }


        const totalSeconds =
            Math.max(
                0,
                Number(seconds)
            );


        const minutes =
            Math.floor(
                totalSeconds / 60
            );


        const remainingSeconds =
            Math.floor(
                totalSeconds % 60
            );


        return `${minutes}m ${remainingSeconds}s`;

    };


    // =========================================================
    // DISTANCE
    // =========================================================

    const distance =
        trajectory &&
        trajectory.distance !== null &&
        trajectory.distance !== undefined &&
        !Number.isNaN(
            Number(trajectory.distance)
        )
            ? Number(trajectory.distance)
            : null;


    // =========================================================
    // DURATION
    // =========================================================

    const duration =
        trajectory &&
        trajectory.duration !== null &&
        trajectory.duration !== undefined &&
        !Number.isNaN(
            Number(trajectory.duration)
        )
            ? Number(trajectory.duration)
            : null;


    // =========================================================
    // AVERAGE SPEED
    // =========================================================

    const averageSpeed =
        trajectory &&
        trajectory.average_speed !== null &&
        trajectory.average_speed !== undefined &&
        !Number.isNaN(
            Number(trajectory.average_speed)
        )
            ? Number(trajectory.average_speed)
            : null;


    // =========================================================
    // DIRECTION
    // =========================================================

    const direction =
        trajectory &&
        trajectory.direction
            ? String(trajectory.direction)
            : null;


    // =========================================================
    // CONFIDENCE
    // =========================================================

    const confidence =
        trajectory &&
        trajectory.confidence !== null &&
        trajectory.confidence !== undefined &&
        !Number.isNaN(
            Number(trajectory.confidence)
        )
            ? Number(trajectory.confidence)
            : null;


    // =========================================================
    // POINTS
    // =========================================================

    const points =
        Array.isArray(
            trajectory?.points
        )
            ? trajectory.points
            : [];


    // =========================================================
    // DIRECTION ARROW
    // =========================================================

    const getDirectionArrow = (value) => {

        switch (value) {

            case 'North':
                return '↑';

            case 'North-East':
                return '↗';

            case 'East':
                return '→';

            case 'South-East':
                return '↘';

            case 'South':
                return '↓';

            case 'South-West':
                return '↙';

            case 'West':
                return '←';

            case 'North-West':
                return '↖';

            default:
                return '—';

        }

    };


    // =========================================================
    // PAGE
    // =========================================================

    return (

        <div className="page-container">


            {/* =====================================================
                HEADER
            ====================================================== */}

            <div className="page-header">

                <div>

                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            marginBottom: '0.25rem'
                        }}
                    >

                        <Link
                            to="/search"
                            style={{
                                color: 'var(--ops-accent)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '0.25rem',
                                fontSize: '0.75rem',
                                textDecoration: 'none',
                                fontFamily: 'var(--font-mono)'
                            }}
                        >

                            <ArrowLeft size={14} />

                            Back to Search

                        </Link>

                    </div>


                    <h1 className="page-title">

                        <Navigation
                            size={24}
                            color="#06b6d4"
                        />

                        Vehicle Trajectory Analysis

                    </h1>


                    <p
                        className="page-subtitle"
                        style={{
                            fontFamily: 'var(--font-mono)'
                        }}
                    >

                        Vehicle ID:{' '}

                        <span
                            style={{
                                color: '#06b6d4',
                                fontWeight: 600
                            }}
                        >

                            {vehicleId}

                        </span>

                    </p>

                </div>


                <div className="clock-badge">

                    <Clock
                        size={14}
                        color="#06b6d4"
                    />

                    Spatial Sequence Tracking

                </div>

            </div>


            {/* =====================================================
                LOADING
            ====================================================== */}

            {loading && (

                <div className="ops-card">

                    <div className="state-container">

                        <div className="state-icon-box">

                            <Loader2
                                size={26}
                                className="animate-spin"
                            />

                        </div>


                        <h3 className="state-title">

                            Loading Trajectory Sequence...

                        </h3>


                        <p className="state-desc">

                            Fetching trajectory points and camera
                            logs for vehicle "{vehicleId}".

                        </p>

                    </div>

                </div>

            )}


            {/* =====================================================
                NO TRAJECTORY
            ====================================================== */}

            {!loading && !trajectory && (

                <div className="ops-card">

                    <div className="state-container">

                        <div
                            className="state-icon-box"
                            style={{
                                color: '#ef4444',
                                backgroundColor:
                                    'var(--alert-critical-bg)',
                                borderColor:
                                    'var(--alert-critical-border)'
                            }}
                        >

                            <FileQuestion size={26} />

                        </div>


                        <h3 className="state-title">

                            No Trajectory Found

                        </h3>


                        <p className="state-desc">

                            {error ||
                                `No movement trajectory sequence registered for vehicle ID "${vehicleId}".`}

                        </p>


                        <Link
                            to="/search"
                            className="ops-button"
                            style={{
                                marginTop: '1rem',
                                textDecoration: 'none'
                            }}
                        >

                            <ArrowLeft size={16} />

                            Return to Search

                        </Link>

                    </div>

                </div>

            )}


            {/* =====================================================
                TRAJECTORY CONTENT
            ====================================================== */}

            {!loading && trajectory && (

                <>


                    {/* =================================================
                        SUMMARY CARDS
                    ================================================== */}

                    <div className="card-grid">


                        {/* =================================================
                            START / END
                        ================================================== */}

                        <div className="ops-card">

                            <div className="card-header">

                                <span className="card-label">

                                    Start & End Time

                                </span>


                                <Calendar
                                    size={18}
                                    color="#06b6d4"
                                />

                            </div>


                            <div
                                style={{
                                    marginTop: '0.5rem',
                                    fontFamily: 'var(--font-mono)',
                                    fontSize: '0.8125rem'
                                }}
                            >

                                <div>

                                    <span
                                        style={{
                                            color:
                                                'var(--ops-text-muted)'
                                        }}
                                    >

                                        Start:

                                    </span>{' '}

                                    {formatDate(
                                        trajectory.start_time
                                    )}

                                </div>


                                <div
                                    style={{
                                        marginTop: '0.25rem'
                                    }}
                                >

                                    <span
                                        style={{
                                            color:
                                                'var(--ops-text-muted)'
                                        }}
                                    >

                                        End:

                                    </span>{' '}

                                    {formatDate(
                                        trajectory.end_time
                                    )}

                                </div>

                            </div>

                        </div>


                        {/* =================================================
                            DISTANCE
                        ================================================== */}

                        <div className="ops-card">

                            <div className="card-header">

                                <span className="card-label">

                                    Distance Traveled

                                </span>


                                <MapPin
                                    size={18}
                                    color="#10b981"
                                />

                            </div>


                            <p className="card-value">

                                {distance !== null
                                    ? `${distance.toFixed(2)} km`
                                    : 'N/A'}

                            </p>


                            <span className="card-subtext text-emerald">

                                {distance !== null
                                    ? 'Geographic Distance'
                                    : 'Distance Not Available'}

                            </span>

                        </div>


                        {/* =================================================
                            DURATION
                        ================================================== */}

                        <div className="ops-card">

                            <div className="card-header">

                                <span className="card-label">

                                    Travel Duration

                                </span>


                                <Clock
                                    size={18}
                                    color="#818cf8"
                                />

                            </div>


                            <p className="card-value">

                                {duration !== null
                                    ? formatDuration(duration)
                                    : 'N/A'}

                            </p>


                            <span
                                className="card-subtext"
                                style={{
                                    color: '#818cf8'
                                }}
                            >

                                Total Transit Time

                            </span>

                        </div>


                        {/* =================================================
                            AVERAGE SPEED
                        ================================================== */}

                        <div className="ops-card">

                            <div className="card-header">

                                <span className="card-label">

                                    Average Speed

                                </span>


                                <Gauge
                                    size={18}
                                    color="#f59e0b"
                                />

                            </div>


                            <p className="card-value">

                                {averageSpeed !== null
                                    ? `${averageSpeed.toFixed(2)} km/h`
                                    : 'N/A'}

                            </p>


                            <span
                                className="card-subtext"
                                style={{
                                    color: '#f59e0b'
                                }}
                            >

                                Distance ÷ Travel Time

                            </span>

                        </div>


                        {/* =================================================
                            DIRECTION
                        ================================================== */}

                        <div className="ops-card">

                            <div className="card-header">

                                <span className="card-label">

                                    Direction of Travel

                                </span>


                                <Navigation
                                    size={18}
                                    color="#8b5cf6"
                                />

                            </div>


                            <p
                                className="card-value"
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                }}
                            >

                                <span
                                    style={{
                                        fontSize: '1.5rem',
                                        color: '#8b5cf6'
                                    }}
                                >

                                    {getDirectionArrow(
                                        direction
                                    )}

                                </span>


                                {direction || 'N/A'}

                            </p>


                            <span
                                className="card-subtext"
                                style={{
                                    color: '#8b5cf6'
                                }}
                            >

                                Geographic Bearing

                            </span>

                        </div>


                        {/* =================================================
                            CONFIDENCE
                        ================================================== */}

                        <div className="ops-card">

                            <div className="card-header">

                                <span className="card-label">

                                    Detection Confidence

                                </span>


                                <ShieldCheck
                                    size={18}
                                    color="#06b6d4"
                                />

                            </div>


                            <p className="card-value text-cyan">

                                {confidence !== null
                                    ? `${Math.round(
                                        confidence * 100
                                    )}%`
                                    : 'N/A'}

                            </p>


                            <span className="card-subtext text-cyan">

                                OCR Detection Confidence

                            </span>

                        </div>

                    </div>


                    {/* =================================================
                        MAP
                    ================================================== */}

                    <div
                        className="ops-card"
                        style={{
                            padding: '1rem'
                        }}
                    >

                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent:
                                    'space-between',
                                marginBottom: '0.75rem',
                                borderBottom:
                                    '1px solid var(--ops-border)',
                                paddingBottom: '0.5rem'
                            }}
                        >

                            <div
                                style={{
                                    fontSize: '0.875rem',
                                    fontWeight: 700,
                                    textTransform:
                                        'uppercase',
                                    color:
                                        'var(--ops-text)',
                                    display: 'flex',
                                    alignItems:
                                        'center',
                                    gap: '0.5rem'
                                }}
                            >

                                <Gauge
                                    size={16}
                                    color="#06b6d4"
                                />

                                Geospatial Camera Sequence Path

                            </div>


                            <span
                                style={{
                                    fontSize: '0.6875rem',
                                    fontFamily:
                                        'var(--font-mono)',
                                    color:
                                        'var(--ops-accent)'
                                }}
                            >

                                {points.length} WAYPOINT
                                {points.length === 1
                                    ? ''
                                    : 'S'}

                            </span>

                        </div>


                        <TrajectoryMap
                            points={points}
                            cameraMap={cameraMap}
                        />

                    </div>


                    {/* =================================================
                        WAYPOINT TABLE
                    ================================================== */}

                    <div className="ops-card">

                        <div
                            style={{
                                fontSize: '0.875rem',
                                fontWeight: 700,
                                textTransform:
                                    'uppercase',
                                color:
                                    'var(--ops-text)',
                                marginBottom:
                                    '0.75rem',
                                display: 'flex',
                                alignItems:
                                    'center',
                                gap: '0.5rem'
                            }}
                        >

                            <MapPin
                                size={16}
                                color="#818cf8"
                            />

                            Trajectory Waypoint Points Sequence

                        </div>


                        <div className="search-table-wrapper">

                            <table className="ops-table">

                                <thead>

                                    <tr>

                                        <th>
                                            #
                                        </th>

                                        <th>
                                            Camera Name
                                        </th>

                                        <th>
                                            Timestamp
                                        </th>

                                        <th>
                                            Location (Coords)
                                        </th>

                                        <th>
                                            Confidence
                                        </th>

                                    </tr>

                                </thead>


                                <tbody>

                                    {points.length > 0 ? (

                                        points.map(
                                            (point, index) => {

                                                const cameraName =
                                                    cameraMap[
                                                        point.camera_id
                                                    ] ||
                                                    point.camera_id ||
                                                    `Camera Node #${index + 1}`;


                                                const pointConfidence =
                                                    point.confidence !==
                                                        null &&
                                                    point.confidence !==
                                                        undefined &&
                                                    !Number.isNaN(
                                                        Number(
                                                            point.confidence
                                                        )
                                                    )
                                                        ? Number(
                                                            point.confidence
                                                        )
                                                        : null;


                                                return (

                                                    <tr
                                                        key={
                                                            point.point_id ||
                                                            index
                                                        }
                                                    >

                                                        <td
                                                            style={{
                                                                fontFamily:
                                                                    'var(--font-mono)',
                                                                fontWeight:
                                                                    700,
                                                                color:
                                                                    'var(--ops-accent)'
                                                            }}
                                                        >

                                                            #{index + 1}

                                                        </td>


                                                        <td
                                                            style={{
                                                                fontWeight:
                                                                    600
                                                            }}
                                                        >

                                                            {cameraName}

                                                        </td>


                                                        <td
                                                            style={{
                                                                fontFamily:
                                                                    'var(--font-mono)',
                                                                fontSize:
                                                                    '0.8125rem'
                                                            }}
                                                        >

                                                            {formatDate(
                                                                point.timestamp
                                                            )}

                                                        </td>


                                                        <td
                                                            style={{
                                                                fontFamily:
                                                                    'var(--font-mono)',
                                                                fontSize:
                                                                    '0.75rem',
                                                                color:
                                                                    'var(--ops-text-muted)'
                                                            }}
                                                        >

                                                            {typeof point.location ===
                                                            'string'
                                                                ? point.location
                                                                : JSON.stringify(
                                                                    point.location
                                                                )}

                                                        </td>


                                                        <td>

                                                            <span
                                                                className="card-subtext text-emerald"
                                                                style={{
                                                                    fontFamily:
                                                                        'var(--font-mono)',
                                                                    fontWeight:
                                                                        700
                                                                }}
                                                            >

                                                                {pointConfidence !==
                                                                    null
                                                                    ? `${Math.round(
                                                                        pointConfidence *
                                                                        100
                                                                    )}%`
                                                                    : 'N/A'}

                                                            </span>

                                                        </td>

                                                    </tr>

                                                );

                                            }
                                        )

                                    ) : (

                                        <tr>

                                            <td
                                                colSpan="5"
                                                style={{
                                                    textAlign:
                                                        'center',
                                                    padding:
                                                        '2rem',
                                                    color:
                                                        'var(--ops-text-muted)'
                                                }}
                                            >

                                                No trajectory
                                                points available.

                                            </td>

                                        </tr>

                                    )}

                                </tbody>

                            </table>

                        </div>

                    </div>

                </>

            )}

        </div>

    );

};


export default TrajectoryPage;