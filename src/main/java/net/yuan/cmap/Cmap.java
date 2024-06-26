package net.yuan.cmap;

import com.mojang.logging.LogUtils;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStartingEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;

@Mod(Cmap.MOD_ID)
public class Cmap {
    public static final String MOD_ID = "cmap";
    private static final Logger LOGGER = LogUtils.getLogger();

    private double lastX = Double.NaN;
    private double lastZ = Double.NaN;

    private PrintWriter overworldPrintWriter;
    private PrintWriter netherPrintWriter;
    private PrintWriter endPrintWriter;

    public Cmap() {
        IEventBus modEventBus = FMLJavaModLoadingContext.get().getModEventBus();
        modEventBus.addListener(this::commonSetup);
        MinecraftForge.EVENT_BUS.register(this);
        modEventBus.addListener(this::addCreative);
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, Config.SPEC);

        try {
            overworldPrintWriter = new PrintWriter(new FileWriter("minecraft_overworld_player_coordinates.txt", true));
            netherPrintWriter = new PrintWriter(new FileWriter("minecraft_the_nether_player_coordinates.txt", true));
            endPrintWriter = new PrintWriter(new FileWriter("minecraft_the_end_player_coordinates.txt", true));
        } catch (IOException e) {
            LOGGER.error("Error initializing PrintWriter", e);
        }
    }

    private void commonSetup(final FMLCommonSetupEvent event) {
    }
    private void addCreative(BuildCreativeModeTabContentsEvent event) {
    }

    @SubscribeEvent
    public void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase == TickEvent.Phase.START) {
            Player player = event.player;
            double x = player.getX();
            double z = player.getZ();
            ResourceKey<Level> currentDimension = player.level().dimension();

            if (x != lastX || z != lastZ) {
                lastX = x;
                lastZ = z;

                if (currentDimension == Level.OVERWORLD) {
                    overworldPrintWriter.println(x + ", " + z);
                    overworldPrintWriter.flush();
                } else if (currentDimension == Level.NETHER) {
                    netherPrintWriter.println(x + ", " + z);
                    netherPrintWriter.flush();
                } else if (currentDimension == Level.END) {
                    endPrintWriter.println(x + ", " + z);
                    endPrintWriter.flush();
                }
            }
        }
    }

    @SubscribeEvent
    public void onServerStarting(ServerStartingEvent event) {
    }

    @Mod.EventBusSubscriber(modid = MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static class ClientModEvents {
        @SubscribeEvent
        public static void onClientSetup(FMLClientSetupEvent event) {
        }
    }
}
