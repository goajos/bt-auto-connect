#!/usr/bin/env uv
import asyncio

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
from dbus_next.signature import Variant

DEVICE_MAC = "FC:91:5D:6C:BB:C5"
MANAGER_IFACE = "org.freedesktop.DBus.ObjectManager"
ADAPTER_IFACE = "org.bluez.Adapter1"
DEVICE_IFACE = "org.bluez.Device1"
PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
BLUEZ_BUS = "org.bluez"

SLEEP_TIMER = 5


async def get_managed_objects(bus) -> dict:
    introspection = await bus.introspect(BLUEZ_BUS, "/")
    obj = bus.get_proxy_object(BLUEZ_BUS, "/", introspection)
    mgr = obj.get_interface(MANAGER_IFACE)
    return await mgr.call_get_managed_objects()


async def find_adapter(bus) -> str | None:
    objects = await get_managed_objects(bus)
    for path, interfaces in objects.items():
        if ADAPTER_IFACE in interfaces:
            return path
    return None


async def find_device(bus, mac_address) -> str | None:
    objects = await get_managed_objects(bus)
    for path, interfaces in objects.items():
        if DEVICE_IFACE in interfaces:
            device = interfaces[DEVICE_IFACE]
            if device.get("Address") == Variant("s", mac_address):
                return path
    return None


async def bt_auto_connect():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    adapter_path = await find_adapter(bus)
    if adapter_path:
        introspection = await bus.introspect(BLUEZ_BUS, adapter_path)
        adapter_obj = bus.get_proxy_object(BLUEZ_BUS, adapter_path, introspection)
        adapter = adapter_obj.get_interface(ADAPTER_IFACE)
        adapter_props = adapter_obj.get_interface(PROPERTIES_IFACE)

        await adapter_props.call_set(ADAPTER_IFACE, "Powered", Variant("b", True))
        try:
            await adapter.call_start_discovery()
        except Exception:
            pass

        while True:
            device_path = await find_device(bus, DEVICE_MAC)
            if device_path:
                introspection = await bus.introspect(BLUEZ_BUS, device_path)
                device_obj = bus.get_proxy_object(BLUEZ_BUS, device_path, introspection)
                device = device_obj.get_interface(DEVICE_IFACE)
                device_props = device_obj.get_interface(PROPERTIES_IFACE)

                trusted = await device_props.call_get(DEVICE_IFACE, "Trusted")
                if not trusted:
                    await device_props.call_set(
                        DEVICE_IFACE, "Trusted", Variant("b", True)
                    )

                paired = await device_props.call_get(DEVICE_IFACE, "Paired")
                if not paired:
                    await device_props.call_set(
                        DEVICE_IFACE, "Paired", Variant("b", True)
                    )
                connected = await device_props.call_get(DEVICE_IFACE, "Connected")
                if not connected:
                    try:
                        await device.call_connect()
                        print(f"Connected to {DEVICE_MAC}")
                    except Exception:
                        pass

            await asyncio.sleep(SLEEP_TIMER)
