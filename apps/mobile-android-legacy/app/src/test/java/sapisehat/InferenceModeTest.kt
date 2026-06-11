package sapisehat

import org.junit.Assert.assertEquals
import org.junit.Test
import com.sapisehat.app.domain.model.InferenceMode

class InferenceModeTest {
    @Test
    fun `enum contains required inference modes`() {
        assertEquals(
            setOf("ONLINE", "OFFLINE", "OFFLINE_FALLBACK"),
            InferenceMode.entries.map { it.name }.toSet()
        )
    }
}
