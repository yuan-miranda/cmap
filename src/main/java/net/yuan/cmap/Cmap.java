package net.yuan.cmap;

import com.mojang.logging.LogUtils;
import net.minecraft.world.entity.player.Player;
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

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.CopyOnWriteArrayList;

// The value here should match an entry in the META-INF/mods.toml file
@Mod(Cmap.MOD_ID)
public class Cmap {
    // Define mod id in a common place for everything to reference
    public static final String MOD_ID = "cmap";
    // Directly reference a slf4j logger
    private static final Logger LOGGER = LogUtils.getLogger();

    private double lastX = Double.NaN;
    private double lastZ = Double.NaN;

    private PrintWriter writer;
    private List<String> coordinateBuffer;
    private Timer timer;

    public Cmap() {
        IEventBus modEventBus = FMLJavaModLoadingContext.get().getModEventBus();

        // Register the commonSetup method for modloading
        modEventBus.addListener(this::commonSetup);

        // Register ourselves for server and other game events we are interested in
        MinecraftForge.EVENT_BUS.register(this);

        // Register the item to a creative tab
        modEventBus.addListener(this::addCreative);

        // Register our mod's ForgeConfigSpec so that Forge can create and load the config file for us
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, Config.SPEC);

        try {
            File file = new File("player_coordinates.txt");
            FileWriter fw = new FileWriter(file, true);
            writer = new PrintWriter(fw);
        } catch (IOException e) {
            LOGGER.error("Error initializing PrintWriter", e);
        }

        // Use CopyOnWriteArrayList for thread-safe access
        coordinateBuffer = new CopyOnWriteArrayList<>();
        timer = new Timer();
        scheduleWriteTask();
    }

    private void commonSetup(final FMLCommonSetupEvent event) {
    }

    // Add the example block item to the building blocks tab
    private void addCreative(BuildCreativeModeTabContentsEvent event) {
    }

    @SubscribeEvent
    public void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase == TickEvent.Phase.START) {
            Player player = event.player;
            double x = player.getX();
            double z = player.getZ();

            if (x != lastX || z != lastZ) {
                lastX = x;
                lastZ = z;
                coordinateBuffer.add(x + ", " + z);
            }
        }
    }

    private void scheduleWriteTask() {
        timer.schedule(new TimerTask() {
            @Override
            public void run() {
                writeCoordinatesToFile();
            }
        }, 1000, 1000);
    }

    private void writeCoordinatesToFile() {
        if (!coordinateBuffer.isEmpty()) {
            if (writer != null) {
                for (String coordinates : coordinateBuffer) {
                    writer.println(coordinates);
                }
                writer.flush();
            }
            coordinateBuffer.clear();
        }
    }

    // You can use SubscribeEvent and let the Event Bus discover methods to call
    @SubscribeEvent
    public void onServerStarting(ServerStartingEvent event) {
    }

    // You can use EventBusSubscriber to automatically register all static methods in the class annotated with @SubscribeEvent
    @Mod.EventBusSubscriber(modid = MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static class ClientModEvents {
        @SubscribeEvent
        public static void onClientSetup(FMLClientSetupEvent event) {
        }
    }
}
