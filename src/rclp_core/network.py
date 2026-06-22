from __future__ import annotations

from rclp_core.models import NetworkProfile, NetworkState


PROFILES: dict[NetworkProfile, NetworkState] = {
    NetworkProfile.NORMAL: NetworkState(
        profile=NetworkProfile.NORMAL,
        latency_ms_p95=45,
        packet_loss_pct=0.1,
        uplink_mbps=8.0,
    ),
    NetworkProfile.DEGRADED_TELEOP: NetworkState(
        profile=NetworkProfile.DEGRADED_TELEOP,
        latency_ms_p95=180,
        packet_loss_pct=3.5,
        uplink_mbps=1.0,
    ),
    NetworkProfile.UPLINK_BAD: NetworkState(
        profile=NetworkProfile.UPLINK_BAD,
        latency_ms_p95=70,
        packet_loss_pct=0.5,
        uplink_mbps=0.6,
    ),
    NetworkProfile.PARTITION: NetworkState(
        profile=NetworkProfile.PARTITION,
        attached=False,
        latency_ms_p95=9999,
        packet_loss_pct=100.0,
        uplink_mbps=0.0,
    ),
}


def profile(name: str | NetworkProfile) -> NetworkState:
    network_profile = NetworkProfile(name)
    if network_profile not in PROFILES:
        raise KeyError(f"unknown deterministic network profile: {name}")
    return PROFILES[network_profile].model_copy(deep=True)


def profile_names() -> list[str]:
    return [network_profile.value for network_profile in PROFILES]
