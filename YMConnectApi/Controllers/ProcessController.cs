using Microsoft.AspNetCore.Mvc;
using YMConnectApi.Services;
using YMConnect;

[Route("[controller]")]
[ApiController]

public class ProcessController : ControllerBase
{

    private readonly RobotService _robotService; // se crea el objeto para utilizar el servicio de conexion al robot

    public ProcessController(RobotService robotService) // este es un constructor de la clase para iniciar el objeto
    {
        _robotService = robotService;
    }

    // este metodo se encarga de cambiar el trabajo activo, se devuelve el estado del robot [codigo 0 es que todo esta bien]
    [HttpGet("setJob")]
    public IActionResult SetJob([FromQuery] string nombre, [FromQuery] string robot_ip)
    {
        try
        {
            var c = _robotService.OpenConnection(robot_ip, out StatusInfo status);
            if (c == null) return StatusCode(500, "No se pudo establecer una conexion");

            status = c.Job.SetActiveJob(nombre, 0);

            _robotService.CloseConnection(c);
            return Ok(status);
        }
        catch (Exception ex)
        {
            return StatusCode(500, "Error al obtener el estado del robot: " + ex.Message);
        }
    }

    /* por ahora no se usa, quizas mas adelante si
    // este metodo obtiene la informacion del JOB que se esta ejecutando en el momento
    [HttpGet("exeJob")]
    public IActionResult GetExecutingData([FromQuery] string robot_ip)
    {
        try
        {
            var c = _robotService.OpenConnection(robot_ip, out StatusInfo status);
            if (c == null) return StatusCode(500, "No se pudo establecer una conexion");

            status = c.Job.GetExecutingJobInformation(InformTaskNumber.Master, out JobData jobData);
            _robotService.CloseConnection(c);
            return Ok(jobData);
        }
        catch (Exception ex)
        {
            return StatusCode(500, "Error al obtener el estado del robot: " + ex.Message);
        }
    }
    */

    // este metodo se encarga de iniciar el JOB activo del robot
    [HttpGet("startJob")]
    public IActionResult StartJob([FromQuery] string robot_ip)
    {
        try
        {
            var c = _robotService.OpenConnection(robot_ip, out StatusInfo status);
            if (c == null) return StatusCode(500, "No se pudo establecer una conexion");

            status = c.ControlCommands.SetCycleMode(CycleMode.Cycle);
            status = c.ControlCommands.SetServos(SignalStatus.ON);
            status = c.ControlCommands.StartJob();

            _robotService.CloseConnection(c);
            return Ok(status);
        }
        catch (Exception ex)
        {
            return StatusCode(500, "Error al obtener el estado del robot: " + ex.Message);
        }
    }

    // funcionalidad para detener el robot mientras se esta ejecutando un JOB se detiene solamente apagando servos
    [HttpGet("stopJob")]
    public IActionResult StopJob([FromQuery] string robot_ip)
    {
        try
        {
            var c = _robotService.OpenConnection(robot_ip, out StatusInfo status);
            if (c == null) return StatusCode(500, "No se pudo establecer una conexion");

            status = c.ControlCommands.SetServos(SignalStatus.OFF);

            _robotService.CloseConnection(c);
            return Ok(status);
        }
        catch (Exception ex)
        {
            return StatusCode(500, "Error al obtener el estado del robot: " + ex.Message);
        }
    }

    /* fue el primer metodo que funciono, lo guardo por cariño
    // METODO PARA CAMBIAR EL CICLO, AQUI ES DE PRUEBA NADA MAS
    [HttpGet("changeCycle")]
    public IActionResult SetCycleMode([FromQuery] string robot_ip)
    {
        try
        {
            var c = _robotService.OpenConnection(robot_ip, out StatusInfo status);
            if (c == null) return StatusCode(500, "No se pudo establecer una conexion");

            status = c.ControlCommands.SetCycleMode(CycleMode.Automatic);

            _robotService.CloseConnection(c);
            return Ok(status);
        }
        catch (Exception ex)
        {
            return StatusCode(500, "Error al obtener alarmas del robot: " + ex.Message);
        }
    }
    */

    [HttpGet("coordinates")] // este metodo nos trae las coordenadas del robot, forzosamente tiene que encontrarse en REMOTE MODE para poder leer sus datos
    public IActionResult GetCoordinates([FromQuery] string robot_ip)
    {
        try
        {
            var c = _robotService.OpenConnection(robot_ip, out StatusInfo status);

            if (c == null) return StatusCode(500, "No se pudo establecer una conexion");

            status = c.ControlGroup.ReadPositionData(ControlGroupId.R1, CoordinateType.Pulse, 1, 0, out PositionData positionData);

            Console.WriteLine(positionData);
            _robotService.CloseConnection(c);
            return Ok(positionData.AxisData);
        }
        catch (Exception ex)
        {
            return StatusCode(500, "Error al obtener el estado del robot: " + ex.Message);
        }
    }

}

/*

INFORMACION IMPORTANTE
En la funcion de las coordenadas se devuelve un objeto de la clase AxisData que luce algo asi:
 
AxisData
    S: 4582 pulse
    L: -55615 pulse
    U: -7 pulse
    R: -7399 pulse
    B: 0 pulse
    T: 0 pulse
    E: 0 pulse
    W: 0 pulse
    
*/